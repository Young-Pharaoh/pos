# Inventory & Sales

A single-shop desktop system for tracking products, recording stock purchases,
completing sales, and generating reports. One operator, one SQLite database,
bilingual product names (Arabic and Spanish).

## Products

**Product**:
A sellable item with bilingual names, a current stock level, a sell price, and
a purchase price reflecting weighted-average unit cost.
_Avoid_: Item (internal name), SKU, article

**Purchase price**:
The product's current weighted-average unit cost, stored on the product and
used for inventory valuation and as the cost basis for future sales.
_Avoid_: Cost, unit cost (reserved for sale-time snapshots), buy price

**Sell price**:
The unit price charged to customers at the time of sale.
_Avoid_: Retail price, list price

**Stock**:
The whole-number quantity of units currently on hand for a product.
_Avoid_: Inventory (use only when referring to the whole catalog), quantity on hand

## Purchases & sales

**Stock purchase**:
An immutable record of units received at a specific unit price on a given date.
Each purchase contributes to the product's weighted-average purchase price.
_Avoid_: Purchase order, receipt, restock event

**Sale**:
A completed customer transaction. Each line stores sell price and unit cost
frozen at completion time.
_Avoid_: Order, transaction, ticket

**Unit cost (on a sale line)**:
The product's purchase price at the exact moment the sale was completed.
Never recalculated when the product's purchase price changes later.
_Avoid_: Purchase price (when referring to historical sale data)

## Costing

**Weighted-average cost**:
The purchase price recalculated after each stock purchase as
(old stock × old average + new quantity × new unit price) ÷ total stock.
_Avoid_: Moving average, FIFO, LIFO
