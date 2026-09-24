# Palyt - Kitchen Stock and Menu Sync

A lightweight kitchen inventory management and live menu availability system. When orders are placed, ingredient stock is deducted in real-time, and dishes automatically become unavailable if any required ingredient falls below its par level buffer.

---

## Tech Stack

- **Backend**: Python 3, Flask, Flask-CORS
- **Storage**: JSON file persistence (`backend/data/stock.json`, `backend/data/recipes.json`)
- **Testing**: `pytest`
- **Frontend**: Plain HTML5, CSS3, Vanilla JavaScript

---

## Setup & Running

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run backend
```bash
python backend/app.py
```

### 3. Open in browser
Open **`http://127.0.0.1:5000`** in your browser.

---

## Running Tests

Run all unit and integration tests with pytest:

```bash
python -m pytest backend/tests/ -v
```

---

## API Endpoints

- `GET /api/health`: Health status.
- `GET /api/inventory`: List all ingredients with stock quantities, par buffers, and dependent dishes.
- `POST /api/inventory`: Add a new ingredient (`{"name": "...", "qty": 100, "unit": "g", "par": 20}`).
- `PUT /api/inventory/<name>` : Update stock quantity or par buffer (`{"qty": 500, "par": 100}`).
- `DELETE /api/inventory/<name>`: Delete an ingredient from stock.
- `GET /api/inventory/<name>/impact`: View dishes that use this ingredient before deleting.
- `GET /api/menu`: List all menu dishes with current availability and reasons if unavailable.
- `POST /api/orders`: Place an order (`{"dish": "Paneer Butter Masala", "servings": 2}`).
- `POST /api/reset`: Reset inventory to initial starter values.

---

## The Write-Up

### 1. The calls made

- **Missing stock items**: In `recipes.json`, some recipes need ingredients that were not present in `stock.json` (such as `Cumin Seeds` in *Veg Pulao* and *Jeera Rice*, and `Refined Flour` in *Butter Naan*). Rather than throwing uncaught server errors or making up stock numbers, the availability checker identifies these as `"missing"` and marks the dish as unavailable with a clear message: `"Missing ingredient in stock: 'Cumin Seeds'"`.
- **Deleting ingredients (`Cashews` vs `Bay Leaves`)**:
  - `Bay Leaves` is not used in any recipe, so deleting it has no effect on the menu.
  - `Cashews` is used in *Paneer Butter Masala* and *Shahi Paneer Korma*. When deleting an ingredient, the frontend checks `/api/inventory/<name>/impact` and warns the user with the list of impacted dishes. Once deleted, the recipes stay in the system, but the dishes become unavailable because the required ingredient is missing from stock.
- **Portion size vs par buffer**: In `Veg Pulao`, `Green Peas` has 30g in stock with a 10g par buffer, but 1 portion requires 50g. Although stock is above par ($30\text{g} > 10\text{g}$), there is not enough stock to cook 1 portion. The availability logic requires both: $\text{stock} \ge \text{par}$ and $\text{stock} \ge \text{recipe portion quantity}$.

### 2. How we checked

- Unit conversion tests check conversions like $1.4\text{ kg} - 180\text{ g} = 1.22\text{ kg}$ and verify that incompatible units (like `kg` to `ml`) fail gracefully.
- Ordering tests verify that ordering 4 servings of *Paneer Butter Masala* uses 60g Cashews, dropping Cashews from 300g to 240g ($< 250\text{g}$ par), which instantly marks both *Paneer Butter Masala* and *Shahi Paneer Korma* as unavailable.
- Restocking Cashews to 500g brings both dishes back to available status.
- What would have to be wrong for tests to pass? If tests only checked boolean status rather than exact post-deduction values, incorrect unit math could slip by. All tests explicitly assert numerical values in the stock's native unit.

### 3. Another day

- Add WebSockets / Server-Sent Events for multi-device sync between the kitchen and diner screens.
- Add an automated low-stock reorder alert when stock falls below par.
- Add support for ingredient substitutes.

---

## Git Workflow

- Initial baseline committed on `main`.
- Development done on feature branch `feature/kitchen-stock-menu`.
- Pull request opened from `feature/kitchen-stock-menu` into `main`.
