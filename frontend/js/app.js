const API_URL = '';

let stockList = [];
let menuList = [];
let searchFilter = '';
let servingsMap = {};
let editingName = null;
let deletingName = null;

document.addEventListener('DOMContentLoaded', () => {
  setupEvents();
  loadData();
});

function setupEvents() {
  document.getElementById('search-input').addEventListener('input', (e) => {
    searchFilter = e.target.value.toLowerCase().trim();
    renderStock();
  });

  document.getElementById('btn-add-ingredient').addEventListener('click', openAddModal);
  document.getElementById('btn-modal-close').addEventListener('click', closeModal);
  document.getElementById('btn-modal-cancel').addEventListener('click', closeModal);
  document.getElementById('ingredient-form').addEventListener('submit', handleFormSubmit);

  document.getElementById('btn-delete-close').addEventListener('click', closeDeleteModal);
  document.getElementById('btn-delete-cancel').addEventListener('click', closeDeleteModal);
  document.getElementById('btn-delete-confirm').addEventListener('click', confirmDelete);

  document.getElementById('btn-reset').addEventListener('click', handleReset);
  document.getElementById('btn-close-alert').addEventListener('click', () => {
    document.getElementById('order-alert').classList.add('hidden');
  });
}

async function loadData() {
  try {
    const [stockRes, menuRes] = await Promise.all([
      fetch(`${API_URL}/api/inventory`).then(r => r.json()),
      fetch(`${API_URL}/api/menu`).then(r => r.json())
    ]);

    if (stockRes.success) {
      stockList = stockRes.data;
      renderStock();
    }
    if (menuRes.success) {
      menuList = menuRes.data;
      renderMenu();
    }
  } catch (err) {
    console.error('Error fetching data:', err);
  }
}

function renderStock() {
  const tbody = document.getElementById('stock-tbody');
  const filtered = stockList.filter(item => !searchFilter || item.name.toLowerCase().includes(searchFilter));

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="muted">No ingredients found.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(item => {
    const isBelow = item.is_below_par;
    const usedIn = item.used_in_dishes || [];
    const usedText = usedIn.length > 0 ? usedIn.join(', ') : '-';

    return `
      <tr class="${isBelow ? 'below-par' : ''}">
        <td><strong>${escapeHtml(item.name)}</strong></td>
        <td>${item.qty} ${item.unit}</td>
        <td>${item.par} ${item.unit}</td>
        <td>
          <span class="badge ${isBelow ? 'badge-bad' : 'badge-ok'}">
            ${isBelow ? 'Below Par' : 'In Stock'}
          </span>
        </td>
        <td>${escapeHtml(usedText)}</td>
        <td>
          <div class="table-actions">
            <button class="btn btn-secondary btn-sm" onclick="openEditModal('${escapeHtml(item.name)}')">Edit</button>
            <button class="btn btn-secondary btn-sm" onclick="openDeletePrompt('${escapeHtml(item.name)}')">Delete</button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function renderMenu() {
  const grid = document.getElementById('menu-grid');
  if (menuList.length === 0) {
    grid.innerHTML = `<div class="muted">No menu items found.</div>`;
    return;
  }

  grid.innerHTML = menuList.map(dish => {
    const available = dish.is_available;
    const count = servingsMap[dish.dish] || 1;
    const ings = dish.ingredients.map(i => `${i.name} (${i.required_qty}${i.required_unit})`).join(', ');
    const reason = !available && dish.unavailable_reasons.length > 0 ? dish.unavailable_reasons[0] : null;

    return `
      <div class="dish-card ${available ? 'available' : 'unavailable'}">
        <div class="dish-header">
          <span class="dish-title">${escapeHtml(dish.dish)}</span>
          <span class="dish-price">₹${dish.price}</span>
        </div>
        <div class="dish-ings">${escapeHtml(ings)}</div>
        ${reason ? `<div class="dish-reason">${escapeHtml(reason)}</div>` : ''}
        <div class="dish-footer">
          <div class="servings-box">
            <button onclick="changeServings('${escapeHtml(dish.dish)}', -1)" ${!available ? 'disabled' : ''}>-</button>
            <span>${count}</span>
            <button onclick="changeServings('${escapeHtml(dish.dish)}', 1)" ${!available ? 'disabled' : ''}>+</button>
          </div>
          <button class="btn btn-primary btn-sm" onclick="orderDish('${escapeHtml(dish.dish)}')" ${!available ? 'disabled' : ''}>
            ${available ? `Order (${count}x)` : 'Unavailable'}
          </button>
        </div>
      </div>
    `;
  }).join('');
}

window.changeServings = function(dishName, delta) {
  const cur = servingsMap[dishName] || 1;
  servingsMap[dishName] = Math.max(1, cur + delta);
  renderMenu();
};

window.orderDish = async function(dishName) {
  const count = servingsMap[dishName] || 1;
  try {
    const res = await fetch(`${API_URL}/api/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dish: dishName, servings: count })
    });
    const json = await res.json();

    if (json.success) {
      stockList = json.data.updated_inventory;
      menuList = json.data.updated_menu;
      renderStock();
      renderMenu();

      const deducts = json.data.deductions.map(d => `${d.ingredient} (-${d.deducted_in_stock_unit})`).join(', ');
      showAlert(`Ordered ${count}x ${dishName}. Deducted: ${deducts}`);
    } else {
      alert(json.error || 'Failed to place order');
    }
  } catch (err) {
    console.error('Order error:', err);
    alert('Failed to place order');
  }
};

function openAddModal() {
  editingName = null;
  document.getElementById('modal-title').textContent = 'Add Ingredient';
  document.getElementById('ing-name').value = '';
  document.getElementById('ing-name').disabled = false;
  document.getElementById('ing-qty').value = '';
  document.getElementById('ing-unit').value = 'g';
  document.getElementById('ing-par').value = '';
  document.getElementById('ingredient-modal').classList.remove('hidden');
}

window.openEditModal = function(name) {
  const item = stockList.find(i => i.name.toLowerCase() === name.toLowerCase());
  if (!item) return;

  editingName = item.name;
  document.getElementById('modal-title').textContent = `Edit ${item.name}`;
  document.getElementById('ing-name').value = item.name;
  document.getElementById('ing-name').disabled = true;
  document.getElementById('ing-qty').value = item.qty;
  document.getElementById('ing-unit').value = item.unit;
  document.getElementById('ing-par').value = item.par;
  document.getElementById('ingredient-modal').classList.remove('hidden');
};

function closeModal() {
  document.getElementById('ingredient-modal').classList.add('hidden');
}

async function handleFormSubmit(e) {
  e.preventDefault();
  const name = document.getElementById('ing-name').value.trim();
  const qty = parseFloat(document.getElementById('ing-qty').value);
  const unit = document.getElementById('ing-unit').value;
  const par = parseFloat(document.getElementById('ing-par').value);

  const payload = { name, qty, unit, par };

  try {
    const url = editingName ? `${API_URL}/api/inventory/${encodeURIComponent(editingName)}` : `${API_URL}/api/inventory`;
    const method = editingName ? 'PUT' : 'POST';

    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const json = await res.json();

    if (json.success) {
      closeModal();
      loadData();
    } else {
      alert(json.error || 'Validation error');
    }
  } catch (err) {
    console.error('Save error:', err);
    alert('Error saving ingredient');
  }
}

window.openDeletePrompt = async function(name) {
  deletingName = name;
  document.getElementById('delete-target-name').textContent = name;

  try {
    const res = await fetch(`${API_URL}/api/inventory/${encodeURIComponent(name)}/impact`);
    const json = await res.json();
    const dishes = json.dependent_dishes || [];

    const warningEl = document.getElementById('delete-impact-msg');
    const listEl = document.getElementById('delete-impact-dishes');

    if (dishes.length > 0) {
      warningEl.classList.remove('hidden');
      listEl.innerHTML = dishes.map(d => `<li>${escapeHtml(d)}</li>`).join('');
    } else {
      warningEl.classList.add('hidden');
      listEl.innerHTML = '';
    }

    document.getElementById('delete-modal').classList.remove('hidden');
  } catch (err) {
    document.getElementById('delete-modal').classList.remove('hidden');
  }
};

function closeDeleteModal() {
  document.getElementById('delete-modal').classList.add('hidden');
  deletingName = null;
}

async function confirmDelete() {
  if (!deletingName) return;

  try {
    const res = await fetch(`${API_URL}/api/inventory/${encodeURIComponent(deletingName)}`, {
      method: 'DELETE'
    });
    const json = await res.json();
    if (json.success) {
      closeDeleteModal();
      loadData();
    } else {
      alert(json.error || 'Failed to delete');
    }
  } catch (err) {
    console.error('Delete error:', err);
    alert('Failed to delete');
  }
}

async function handleReset() {
  if (!confirm('Reset stock to baseline values?')) return;
  try {
    const res = await fetch(`${API_URL}/api/reset`, { method: 'POST' });
    const json = await res.json();
    if (json.success) {
      stockList = json.inventory;
      menuList = json.menu;
      renderStock();
      renderMenu();
      document.getElementById('order-alert').classList.add('hidden');
    }
  } catch (err) {
    console.error('Reset error:', err);
  }
}

function showAlert(msg) {
  document.getElementById('order-alert-msg').textContent = msg;
  document.getElementById('order-alert').classList.remove('hidden');
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
