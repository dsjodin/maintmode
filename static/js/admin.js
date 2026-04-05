const API = "/api/v1";
let currentHostname = null;

document.addEventListener("DOMContentLoaded", () => {
  loadSites();
  document.getElementById("add-site-form").addEventListener("submit", addSite);
  document.getElementById("maintenance-form").addEventListener("submit", confirmMaintenance);
});

async function loadSites() {
  try {
    const res = await fetch(`${API}/sites`);
    const sites = await res.json();
    renderSites(sites);
  } catch (err) {
    document.getElementById("sites-list").innerHTML =
      '<p class="error">Failed to load sites.</p>';
  }
}

function renderSites(sites) {
  const container = document.getElementById("sites-list");
  if (sites.length === 0) {
    container.innerHTML = '<p class="empty">No sites registered yet. Add one above.</p>';
    return;
  }
  container.innerHTML = sites
    .map(
      (site) => `
    <div class="site-card ${site.maintenance ? "maintenance-active" : ""}">
      <div class="site-info">
        <h3>${escapeHtml(site.name)}</h3>
        <span class="site-hostname">${escapeHtml(site.hostname)}</span>
        ${
          site.maintenance
            ? `<span class="badge badge-maint">MAINTENANCE</span>`
            : `<span class="badge badge-live">LIVE</span>`
        }
      </div>
      <div class="site-actions">
        ${
          site.maintenance
            ? `<button class="btn btn-success" onclick="disableMaintenance('${escapeAttr(site.hostname)}')">Restore</button>`
            : `<button class="btn btn-warning" onclick="showMaintenanceModal('${escapeAttr(site.hostname)}')">Maintenance</button>`
        }
        <button class="btn btn-danger-outline" onclick="removeSite('${escapeAttr(site.hostname)}')">Remove</button>
      </div>
    </div>
  `
    )
    .join("");
}

async function addSite(e) {
  e.preventDefault();
  const hostname = document.getElementById("hostname").value.trim();
  const name = document.getElementById("sitename").value.trim();
  if (!hostname || !name) return;

  try {
    const res = await fetch(`${API}/sites`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ hostname, name }),
    });
    if (!res.ok) {
      const data = await res.json();
      showToast(data.detail || "Failed to add site", "error");
      return;
    }
    document.getElementById("hostname").value = "";
    document.getElementById("sitename").value = "";
    showToast(`Added ${hostname}`, "success");
    loadSites();
  } catch (err) {
    showToast("Network error", "error");
  }
}

async function removeSite(hostname) {
  if (!confirm(`Remove ${hostname} from the registry?`)) return;
  try {
    const res = await fetch(`${API}/sites/${hostname}`, { method: "DELETE" });
    if (!res.ok && res.status !== 204) {
      showToast("Failed to remove site", "error");
      return;
    }
    showToast(`Removed ${hostname}`, "success");
    loadSites();
  } catch (err) {
    showToast("Network error", "error");
  }
}

function showMaintenanceModal(hostname) {
  currentHostname = hostname;
  document.getElementById("modal-hostname").textContent = hostname;
  document.getElementById("maint-message").value = "";
  document.getElementById("maint-return").value = "";
  document.getElementById("modal-overlay").classList.remove("hidden");
}

function closeModal() {
  document.getElementById("modal-overlay").classList.add("hidden");
  currentHostname = null;
}

async function confirmMaintenance(e) {
  e.preventDefault();
  if (!currentHostname) return;

  const message = document.getElementById("maint-message").value.trim() || null;
  const estimated_return = document.getElementById("maint-return").value.trim() || null;

  try {
    const res = await fetch(`${API}/sites/${currentHostname}/maintenance`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, estimated_return }),
    });
    if (!res.ok) {
      showToast("Failed to enable maintenance", "error");
      return;
    }
    showToast(`Maintenance enabled for ${currentHostname}`, "success");
    closeModal();
    loadSites();
  } catch (err) {
    showToast("Network error", "error");
  }
}

async function disableMaintenance(hostname) {
  try {
    const res = await fetch(`${API}/sites/${hostname}/maintenance`, {
      method: "DELETE",
    });
    if (!res.ok) {
      showToast("Failed to disable maintenance", "error");
      return;
    }
    showToast(`${hostname} is back online`, "success");
    loadSites();
  } catch (err) {
    showToast("Network error", "error");
  }
}

function showToast(message, type) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.className = `toast ${type}`;
  setTimeout(() => {
    toast.className = "toast hidden";
  }, 3000);
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function escapeAttr(str) {
  return str.replace(/'/g, "\\'").replace(/"/g, "&quot;");
}
