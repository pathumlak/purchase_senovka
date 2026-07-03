"""
Backfill CustomerLedger entries for all historical bills.

Usage:
    python manage.py backfill_ledger --settings=erp.settings_local

Run once after deploying the ledger feature. Safe to re-run — it clears
existing ledger entries first so no duplicates are created.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.billing.models import Bill, Payment
from apps.customers.models import Customer, CustomerLedger


_D = Decimal('0')
_TWO = Decimal('0.01')


class Command(BaseCommand):
    help = 'Backfill CustomerLedger entries from existing bills'

    def add_arguments(self, parser):
        parser.add_argument(
            '--customer',
            type=int,
            default=None,
            help='Backfill a single customer by ID (default: all customers)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be created without saving',
        )

    def handle(self, *args, **options):
        customer_id = options['customer']
        dry_run = options['dry_run']

        if customer_id:
            customers = Customer.objects.filter(pk=customer_id)
        else:
            customers = Customer.objects.all().order_by('id')

        total_entries = 0
        for customer in customers:
            count = self._backfill_customer(customer, dry_run)
            total_entries += count
            self.stdout.write(f'  {customer.name}: {count} entries')

        suffix = ' (dry run)' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {total_entries} ledger entries created{suffix}.'
        ))

    @transaction.atomic
    def _backfill_customer(self, customer, dry_run):
        # Clear existing ledger entries so we start fresh
        if not dry_run:
            CustomerLedger.objects.filter(customer=customer).delete()

        bills = (
            Bill.objects
            .filter(customer=customer)
            .exclude(status=Bill.CANCELLED)
            .prefetch_related('payments')
            .order_by('bill_date', 'created_at')
        )

        entries = []
        running_balance = _D  # We'll reconcile at the end

        for bill in bills:
            payments = list(bill.payments.order_by('payment_date', 'id'))
            bill_method = bill.payment_method

            if bill_method == Bill.PAY_LATER:
                # Creation: balance -= total_amount
                running_balance -= bill.total_amount
                entries.append(self._entry(
                    customer, bill, bill.bill_date,
                    f"Sale on Credit - {bill.bill_number}",
                    CustomerLedger.SALE,
                    debit=bill.total_amount, credit=_D,
                    balance=running_balance,
                ))
                # All payments on PAY_LATER bills are settlement payments
                for pmt in payments:
                    if pmt.method == Payment.BALANCE:
                        running_balance -= pmt.amount
                        entries.append(self._entry(
                            customer, bill, pmt.payment_date,
                            f"Credit Balance Used - {bill.bill_number}",
                            CustomerLedger.BALANCE_USED,
                            debit=pmt.amount, credit=_D,
                            balance=running_balance,
                        ))
                    else:
                        running_balance += pmt.amount
                        ltype = CustomerLedger.PAYMENT_CHEQUE if pmt.method == Payment.CHEQUE else CustomerLedger.PAYMENT_CASH
                        entries.append(self._entry(
                            customer, bill, pmt.payment_date,
                            f"Payment Received - {bill.bill_number}",
                            ltype,
                            debit=_D, credit=pmt.amount,
                            balance=running_balance,
                        ))

            elif bill_method in (Bill.FULL_CASH, Bill.FULL_CHEQUE, Bill.MIXED):
                # Balance change at creation = -balance_used + overpayment
                balance_used = bill.balance_used
                overpayment = max(_D, bill.amount_paid - (bill.total_amount - balance_used))
                labels = {Bill.FULL_CASH: 'Cash', Bill.FULL_CHEQUE: 'Cheque', Bill.MIXED: 'Mixed'}
                label = labels.get(bill_method, 'Cash')

                if balance_used > _D or overpayment > _D:
                    running_balance -= balance_used
                    running_balance += overpayment
                    entries.append(self._entry(
                        customer, bill, bill.bill_date,
                        f"Sale ({label}) - {bill.bill_number}",
                        CustomerLedger.SALE_CASH,
                        debit=balance_used, credit=overpayment,
                        balance=running_balance,
                    ))
                else:
                    # Pure cash sale, no balance impact — informational only
                    entries.append(self._entry(
                        customer, bill, bill.bill_date,
                        f"Sale ({label}) - {bill.bill_number}",
                        CustomerLedger.SALE_CASH,
                        debit=bill.total_amount, credit=bill.total_amount,
                        balance=running_balance,
                    ))

            elif bill_method in (Bill.PARTIAL_CASH, Bill.PARTIAL_CHEQUE):
                # No balance change at creation for partial bills.
                # Balance changes only come from settlement payments.
                label = 'Cash' if bill_method == Bill.PARTIAL_CASH else 'Cheque'

                # Identify creation payment: first CASH/CHEQUE payment at bill_date
                creation_pmts = [p for p in payments if p.payment_date == bill.bill_date and p.method != Payment.BALANCE]
                creation_total = sum(p.amount for p in creation_pmts)

                # Informational entry for the sale (no balance change)
                entries.append(self._entry(
                    customer, bill, bill.bill_date,
                    f"Sale ({label}, Partial) - {bill.bill_number}",
                    CustomerLedger.SALE_PARTIAL,
                    debit=bill.total_amount, credit=creation_total,
                    balance=running_balance,
                ))

                # Settlement payments (after bill_date, or BALANCE payments)
                settle_pmts = [p for p in payments if p.payment_date > bill.bill_date or p.method == Payment.BALANCE]
                for pmt in settle_pmts:
                    if pmt.method == Payment.BALANCE:
                        running_balance -= pmt.amount
                        entries.append(self._entry(
                            customer, bill, pmt.payment_date,
                            f"Credit Balance Used - {bill.bill_number}",
                            CustomerLedger.BALANCE_USED,
                            debit=pmt.amount, credit=_D,
                            balance=running_balance,
                        ))
                    else:
                        running_balance += pmt.amount
                        ltype = CustomerLedger.PAYMENT_CHEQUE if pmt.method == Payment.CHEQUE else CustomerLedger.PAYMENT_CASH
                        entries.append(self._entry(
                            customer, bill, pmt.payment_date,
                            f"Payment Received - {bill.bill_number}",
                            ltype,
                            debit=_D, credit=pmt.amount,
                            balance=running_balance,
                        ))

        # Reconcile: if running_balance != customer.balance, add an adjustment entry
        diff = (customer.balance - running_balance).quantize(_TWO)
        if diff != _D:
            from django.utils import timezone
            entries.append(self._entry(
                customer, None, timezone.localdate(),
                'Opening Balance / Adjustment',
                CustomerLedger.MANUAL_ADJUSTMENT,
                debit=max(_D, -diff), credit=max(_D, diff),
                balance=customer.balance,
            ))

        if not dry_run and entries:
            CustomerLedger.objects.bulk_create(entries)

        return len(entries)

    @staticmethod
    def _entry(customer, bill, date, description, transaction_type,
               debit, credit, balance):
        return CustomerLedger(
            customer=customer,
            date=date,
            bill_number=bill.bill_number if bill else '',
            description=description,
            transaction_type=transaction_type,
            debit=debit,
            credit=credit,
            balance=balance,
            bill=bill,
        )
