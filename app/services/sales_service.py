"""Completing a sale: the other place besides ``add_stock`` where a
multi-step change must be all-or-nothing.

``complete_sale`` re-reads every item fresh from the database inside the
transaction rather than trusting the ``SaleDraft`` snapshot, because spec
section 14 defines ``unit_cost`` as the item's purchase price "at that
exact moment" -- the moment of completion, not the moment the line was
added to the draft. The same freshness applies to available stock: the
draft may be minutes old by the time the cashier presses "Complete Sale".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session, sessionmaker

from app.database.models import Sale, SaleItem
from app.database.repositories.item_repository import ItemRepository
from app.database.repositories.sale_repository import SaleRepository
from app.errors import InsufficientStockError, ItemInactiveError, ItemNotFoundError, ValidationError
from app.services.sale_draft import ItemSnapshot, SaleDraft
from app.utils.money import quantize_money


@dataclass(frozen=True)
class SaleReceiptLine:
    item_id: int
    name_ar: str
    name_es: str
    quantity: int
    unit_sell_price: Decimal
    unit_cost: Decimal
    total_sell_price: Decimal
    total_cost: Decimal


@dataclass(frozen=True)
class SaleReceipt:
    id: int
    sale_date: datetime
    total: Decimal
    lines: list[SaleReceiptLine]


class SalesService:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    def resolve_item(self, query: str) -> ItemSnapshot:
        """Resolve a New-Sale search box entry (id or partial name) to a snapshot.

        Exact numeric id match wins first; otherwise falls back to the
        unified name search. Only active items can be sold.
        """
        query = str(query).strip()
        if not query:
            raise ItemNotFoundError(query)

        with self._session_factory() as session:
            items_repo = ItemRepository(session)
            item = None
            if query.isdigit():
                candidate = items_repo.get(int(query))
                if candidate is not None and candidate.is_active:
                    item = candidate

            if item is None:
                matches = items_repo.search(query, include_archived=False)
                if len(matches) == 1:
                    item = matches[0]
                elif len(matches) > 1:
                    exact = [
                        m
                        for m in matches
                        if query.casefold() in (m.name_es.casefold(), m.name_ar.casefold())
                    ]
                    item = exact[0] if exact else matches[0]

            if item is None:
                raise ItemNotFoundError(query)

            return ItemSnapshot(
                id=item.id,
                name_ar=item.name_ar,
                name_es=item.name_es,
                sell_price=item.sell_price,
                cost=item.purchase_price,
                available_stock=item.stock,
            )

    def complete_sale(self, draft: SaleDraft) -> SaleReceipt:
        """Commit the draft in one transaction: sale, sale_items, stock.

        1. Insert the ``sales`` row (flushed to obtain its id).
        2. For each line: re-validate stock, insert ``sale_items`` with a
           freshly-read cost/sell price, and conditionally decrement stock.
        3. Update the sale's total and commit.

        Any failure (missing item, archived item, insufficient stock, or an
        unexpected database error) rolls back the entire transaction, so a
        sale can never be recorded without its stock reduction, and stock
        can never be reduced without the matching sale.
        """
        if draft.is_empty:
            raise ValidationError("sales.empty_sale_message")

        with self._session_factory() as session:
            with session.begin():
                items_repo = ItemRepository(session)
                sales_repo = SaleRepository(session)

                now = datetime.now()
                sale = sales_repo.add_sale(Sale(sale_date=now, total=Decimal("0")))

                lines: list[SaleReceiptLine] = []
                running_total = Decimal("0")

                for draft_line in draft.lines:
                    item = items_repo.get(draft_line.item.id)
                    if item is None:
                        raise ItemNotFoundError(draft_line.item.id)
                    if not item.is_active:
                        raise ItemInactiveError(item.id)

                    quantity = draft_line.quantity
                    unit_sell_price = item.sell_price
                    unit_cost = item.purchase_price
                    total_sell_price = quantize_money(unit_sell_price * quantity)
                    total_cost = quantize_money(unit_cost * quantity)

                    if not sales_repo.decrement_stock(item.id, quantity):
                        raise InsufficientStockError(item.id, quantity, item.stock)

                    sales_repo.add_sale_item(
                        SaleItem(
                            sale_id=sale.id,
                            item_id=item.id,
                            quantity=quantity,
                            unit_sell_price=unit_sell_price,
                            unit_cost=unit_cost,
                            total_sell_price=total_sell_price,
                            total_cost=total_cost,
                        )
                    )

                    running_total += total_sell_price
                    lines.append(
                        SaleReceiptLine(
                            item_id=item.id,
                            name_ar=item.name_ar,
                            name_es=item.name_es,
                            quantity=quantity,
                            unit_sell_price=unit_sell_price,
                            unit_cost=unit_cost,
                            total_sell_price=total_sell_price,
                            total_cost=total_cost,
                        )
                    )

                sale.total = quantize_money(running_total)
                session.flush()
                receipt = SaleReceipt(
                    id=sale.id, sale_date=sale.sale_date, total=sale.total, lines=lines
                )
            return receipt
