window.__ACADEMIC_ADMIN_JS_LOADED__ = true;
const API = "/api/v1";

let token = localStorage.getItem("admin_access_token");
let currentUser = null;
let allServices = [];


const loginView = document.getElementById("loginView");
const appView = document.getElementById("appView");


function showLogin() {
    loginView.classList.remove("hidden");
    appView.classList.add("hidden");
}


function showApp() {
    loginView.classList.add("hidden");
    appView.classList.remove("hidden");
}


async function api(path, options = {}) {
    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {})
    };

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(API + path, {
        ...options,
        headers
    });

    if (response.status === 401) {
        logout();
        throw new Error("Authentication expired.");
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(
            data?.error?.message ||
            data?.detail ||
            "Request failed."
        );
    }

    return data;
}



window.login = async function login(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");

    if (!usernameInput || !passwordInput) {
        alert("Login form fields were not found.");
        return false;
    }

    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    if (!username || !password) {
        alert("Please enter username and password.");
        return false;
    }

    const button =
        document.querySelector("#loginForm button[type='submit']") ||
        document.querySelector("#loginForm button");

    if (button) {
        button.disabled = true;
        button.textContent = "Signing in...";
    }

    try {
        const response = await fetch("/api/v1/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });

        const text = await response.text();

        let data = {};
        try {
            data = text ? JSON.parse(text) : {};
        } catch (e) {
            throw new Error("Server returned an invalid response.");
        }

        if (!response.ok) {
            let message = data.detail || data.message || "Login failed.";

            if (Array.isArray(message)) {
                message = message
                    .map(item => item.msg || String(item))
                    .join(", ");
            }

            throw new Error(message);
        }

        const accessToken = data.access_token || data.token;

        if (!accessToken) {
            throw new Error("No access token was returned by the server.");
        }

        token = accessToken;
        localStorage.setItem("admin_access_token", accessToken);

        // Get current user.
        try {
            const meResponse = await fetch("/api/v1/auth/me", {
                headers: {
                    "Authorization": "Bearer " + accessToken,
                    "Accept": "application/json"
                }
            });

            if (meResponse.ok) {
                currentUser = await meResponse.json();
            }
        } catch (e) {
            console.warn("Could not load current user:", e);
        }

        const loginScreen = document.getElementById("loginScreen");
        const dashboard = document.getElementById("appView");

        if (loginScreen) {
            loginScreen.style.display = "none";
        }

        if (dashboard) {
            dashboard.style.display = "flex";
        }

        if (typeof loadDashboard === "function") {
            await loadDashboard();
        }

        if (typeof openPage === "function") {
            openPage("dashboard");
        }

    } catch (error) {
        console.error("LOGIN ERROR:", error);
        alert(error.message || "Unable to login.");

        localStorage.removeItem("admin_access_token");
        token = null;

    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = "Login";
        }
    }

    return false;
}

async function loadDashboard() {
    try {
        const [users, services] = await Promise.all([
            api("/admin/users?page=1&page_size=1"),
            api("/admin/services?page=1&page_size=1")
        ]);

        document.getElementById("statUsers").textContent = users.total;
        document.getElementById("statServices").textContent = services.total;

        if (currentUser) {
            const name =
                currentUser.first_name ||
                currentUser.username ||
                "Administrator";

            document.getElementById("adminName").textContent = name;
            document.getElementById("adminAvatar").textContent =
                name.charAt(0).toUpperCase();
        }
    } catch (error) {
        console.error(error);
    }
}


async function loadUsers() {
    const search = document.getElementById("userSearch").value.trim();
    const status = document.getElementById("userStatus").value;

    const params = new URLSearchParams({
        page: "1",
        page_size: "50"
    });

    if (search) params.set("search", search);
    if (status) params.set("status", status);

    const table = document.getElementById("usersTable");

    table.innerHTML =
        `<tr><td colspan="5" class="empty">Loading...</td></tr>`;

    try {
        const data = await api(`/admin/users?${params}`);

        document.getElementById("usersTotal").textContent =
            `${data.total} users`;

        if (!data.items.length) {
            table.innerHTML =
                `<tr><td colspan="5" class="empty">No users found.</td></tr>`;
            return;
        }

        table.innerHTML = data.items.map(user => {
            const role =
                user.roles?.map(r => r.name).join(", ") || "—";

            const name =
                [user.first_name, user.last_name]
                    .filter(Boolean)
                    .join(" ") ||
                user.username ||
                "Unnamed";

            const statusClass =
                String(user.status).toLowerCase() === "active"
                    ? "active"
                    : "inactive";

            return `
                <tr>
                    <td>
                        <strong>${escapeHtml(name)}</strong>
                        <br>
                        <small class="muted">
                            ${escapeHtml(user.username || "")}
                        </small>
                    </td>

                    <td>${escapeHtml(user.email || "—")}</td>

                    <td>${escapeHtml(role)}</td>

                    <td>
                        <span class="badge ${statusClass}">
                            ${escapeHtml(user.status)}
                        </span>
                    </td>

                    <td>
                        ${formatDate(user.created_at)}
                    </td>
                </tr>
            `;
        }).join("");

    } catch (error) {
        table.innerHTML =
            `<tr><td colspan="5" class="empty">${escapeHtml(error.message)}</td></tr>`;
    }
}


async function loadServices() {
    const container = document.getElementById("servicesTable");
    if (!container) return;

    container.innerHTML = '<div class="loading">Loading services...</div>';

    try {
        const data = await apiFetch("/admin/services?page=1&page_size=100");

        allServices = data.items || data.services || [];

        renderServices(allServices);
    } catch (error) {
        container.innerHTML = `<div class="error">${escapeHtml(error.message)}</div>`;
    }
}

function renderServices(services) {
    const container = document.getElementById("servicesTable");
    if (!container) return;

    if (!services.length) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <h3>No services found</h3>
                <p>Create a service using the "+ Add Service" button.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="table-wrapper">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Service</th>
                        <th>Category</th>
                        <th>Status</th>
                        <th>Sort</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${services.map(service => `
                        <tr>
                            <td>
                                <div class="service-name">${escapeHtml(service.name || "")}</div>
                                <div class="service-description">
                                    ${escapeHtml(service.short_description || service.description || "")}
                                </div>
                            </td>
                            <td>${escapeHtml(service.category?.name || "—")}</td>
                            <td>
                                <span class="status-badge ${service.is_active ? "status-active" : "status-inactive"}">
                                    ${service.is_active ? "Active" : "Inactive"}
                                </span>
                            </td>
                            <td>${service.sort_order ?? 0}</td>
                            <td>${formatDate(service.created_at)}</td>
                            <td>
                                <div class="service-actions">
                                    <button
                                        class="btn btn-small btn-secondary"
                                        onclick='editService(${JSON.stringify(service).replace(/'/g, "&#39;")})'>
                                        Edit
                                    </button>

                                    <button
                                        class="btn btn-small ${service.is_active ? "btn-danger" : "btn-success"}"
                                        onclick="toggleService('${service.id}', ${service.is_active})">
                                        ${service.is_active ? "Deactivate" : "Activate"}
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        </div>
    `;
}

function filterServices() {
    const search = (document.getElementById("serviceSearch")?.value || "")
        .trim()
        .toLowerCase();

    const status = document.getElementById("serviceStatusFilter")?.value || "all";

    const filtered = allServices.filter(service => {
        const matchesSearch =
            !search ||
            (service.name || "").toLowerCase().includes(search) ||
            (service.short_description || "").toLowerCase().includes(search) ||
            (service.description || "").toLowerCase().includes(search) ||
            (service.category?.name || "").toLowerCase().includes(search);

        const matchesStatus =
            status === "all" ||
            (status === "active" && service.is_active) ||
            (status === "inactive" && !service.is_active);

        return matchesSearch && matchesStatus;
    });

    renderServices(filtered);
}

function editService(service) {
    document.getElementById("serviceEditId").value = service.id;
    document.getElementById("serviceName").value = service.name || "";
    document.getElementById("serviceShortDescription").value =
        service.short_description || "";
    document.getElementById("serviceDescription").value =
        service.description || "";
    document.getElementById("serviceSortOrder").value =
        service.sort_order ?? 0;
    document.getElementById("serviceActive").checked =
        !!service.is_active;

    const category = document.getElementById("serviceCategory");

    if (service.category?.id) {
        category.value = service.category.id;
    }

    document.getElementById("serviceModalTitle").textContent = "Edit Service";
    document.getElementById("serviceSubmitButton").textContent = "Save Changes";

    document.getElementById("serviceModal").classList.add("show");
}

async function toggleService(serviceId, currentlyActive) {
    const action = currentlyActive ? "deactivate" : "activate";

    if (!confirm(`Are you sure you want to ${action} this service?`)) {
        return;
    }

    try {
        await apiFetch(`/admin/services/${serviceId}`, {
            method: "PATCH",
            body: JSON.stringify({
                is_active: !currentlyActive
            })
        });

        alert(`Service ${action}d successfully.`);
        await loadServices();

        if (typeof loadDashboard === "function") {
            await loadDashboard();
        }
    } catch (error) {
        alert(`Operation failed: ${error.message}`);
    }
}

async function toggleService(serviceId, currentlyActive) {
    const action = currentlyActive ? "deactivate" : "activate";

    if (!confirm(`Are you sure you want to ${action} this service?`)) {
        return;
    }

    try {
        await apiFetch(`/admin/services/${serviceId}`, {
            method: "PATCH",
            body: JSON.stringify({
                is_active: !currentlyActive
            })
        });

        alert(`Service ${action}d successfully.`);
        await loadServices();

        if (typeof loadDashboard === "function") {
            await loadDashboard();
        }
    } catch (error) {
        alert(`Operation failed: ${error.message}`);
    }
}

async function loadServiceCategories() {
    const select = document.getElementById("newServiceCategory");
    if (!select) return;

    select.innerHTML = `<option value="">Loading categories...</option>`;

    try {
        /*
         * The current platform already has services with category
         * information. We use the existing category as the initial
         * category source without requiring a new backend endpoint.
         */
        const data = await api("/admin/services?page=1&page_size=50");

        const categories = new Map();

        (data.items || []).forEach(service => {
            if (service.category?.id && service.category?.name) {
                categories.set(service.category.id, service.category.name);
            }
        });

        if (!categories.size) {
            select.innerHTML =
                `<option value="">No category available</option>`;
            return;
        }

        select.innerHTML =
            `<option value="">Select category</option>` +
            Array.from(categories.entries())
                .map(([id, name]) =>
                    `<option value="${escapeHtml(id)}">${escapeHtml(name)}</option>`
                )
                .join("");

    } catch (error) {
        select.innerHTML =
            `<option value="">Unable to load categories</option>`;
    }
}


function openServiceModal() {
    document.getElementById("serviceEditId").value = "";
    document.getElementById("serviceName").value = "";
    document.getElementById("serviceShortDescription").value = "";
    document.getElementById("serviceDescription").value = "";
    document.getElementById("serviceSortOrder").value = "0";
    document.getElementById("serviceActive").checked = true;

    document.getElementById("serviceModalTitle").textContent = "Add Service";
    document.getElementById("serviceSubmitButton").textContent = "Create Service";

    loadServiceCategories();
    document.getElementById("serviceModal").classList.add("show");
}


function closeServiceModal() {
    document.getElementById("serviceModal").classList.add("hidden");
}


async function createService(event) {
    event.preventDefault();

    const error = document.getElementById("serviceFormError");
    error.classList.add("hidden");

    const name =
        document.getElementById("newServiceName").value.trim();

    const shortDescription =
        document.getElementById("newServiceShortDescription").value.trim();

    const description =
        document.getElementById("newServiceDescription").value.trim();

    const categoryId =
        document.getElementById("newServiceCategory").value;

    const sortOrder =
        Number(document.getElementById("newServiceSortOrder").value || 0);

    const isActive =
        document.getElementById("newServiceActive").checked;

    if (!categoryId) {
        error.textContent = "Please select a category.";
        error.classList.remove("hidden");
        return;
    }

    try {
        await api("/admin/services", {
            method: "POST",
            body: JSON.stringify({
                name,
                short_description: shortDescription || null,
                description: description || null,
                category_id: categoryId,
                sort_order: sortOrder,
                is_active: isActive
            })
        });

        closeServiceModal();

        if (!document.getElementById("servicesPage").classList.contains("hidden")) {
            await loadServices();
        }

        await loadDashboard();

        alert("Service created successfully.");

    } catch (exception) {
        error.textContent = exception.message;
        error.classList.remove("hidden");
    }
}


document.addEventListener("DOMContentLoaded", () => {

    const loginForm = document.getElementById("loginForm");

    if (loginForm) {
        const loginButton = loginForm.querySelector("button[type='submit']");

        if (loginButton) {
            loginButton.addEventListener("click", function (event) {
                event.preventDefault();

                if (typeof window.login === "function") {
                    window.login(event);
                } else {
                    alert("Login script failed to load. Please refresh the Preview.");
                }
            });
        }
    }

    const addButton = document.getElementById("addServiceButton");
    const closeButton = document.getElementById("closeServiceModal");
    const cancelButton = document.getElementById("cancelServiceButton");
    const form = document.getElementById("serviceForm");

    if (addButton) {
        addButton.addEventListener("click", openServiceModal);
    }

    if (closeButton) {
        closeButton.addEventListener("click", closeServiceModal);
    }

    if (cancelButton) {
        cancelButton.addEventListener("click", closeServiceModal);
    }

    if (form) {
        form.addEventListener("submit", createService);
    }
});

async function loadRequests() {
    const tbody = document.getElementById("requestsTableBody");
    if (!tbody) return;

    tbody.innerHTML = `
        <tr>
            <td colspan="8" style="text-align:center;">Loading requests...</td>
        </tr>
    `;

    try {
        const search = document.getElementById("requestSearch")?.value.trim() || "";
        const status = document.getElementById("requestStatusFilter")?.value || "";
        const priority = document.getElementById("requestPriorityFilter")?.value || "";

        const params = new URLSearchParams({
            page: "1",
            page_size: "100"
        });

        if (search) params.set("search", search);
        if (status) params.set("status", status);
        if (priority) params.set("priority", priority);

        const data = await api(`/admin/requests?${params.toString()}`);

        if (!data.items || data.items.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align:center;">
                        No requests found.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = data.items.map(request => `
            <tr>
                <td>
                    <strong>${escapeHtml(request.title || "—")}</strong>
                    ${request.specialization
                        ? `<div class="muted">${escapeHtml(request.specialization)}</div>`
                        : ""}
                </td>
                <td>${escapeHtml(request.customer_id || "—")}</td>
                <td>${escapeHtml(request.service_id || "—")}</td>
                <td>${escapeHtml(request.status || "—")}</td>
                <td>${escapeHtml(request.priority || "—")}</td>
                <td>${request.deadline ? escapeHtml(request.deadline) : "—"}</td>
                <td>${request.created_at ? escapeHtml(request.created_at) : "—"}</td>
                <td>
                    <button class="btn btn-primary" onclick="viewRequest('${request.id}')">
                        View
                    </button>
                </td>
            </tr>
        `).join("");
    } catch (error) {
        console.error("loadRequests error:", error);

        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align:center;">
                    Failed to load requests.
                </td>
            </tr>
        `;
    }
}

function viewRequest(requestId) {
    alert("Request ID: " + requestId);
}

document.addEventListener("DOMContentLoaded", () => {
    const refresh = document.getElementById("refreshRequestsBtn");
    const search = document.getElementById("requestSearch");
    const status = document.getElementById("requestStatusFilter");
    const priority = document.getElementById("requestPriorityFilter");

    if (refresh) refresh.addEventListener("click", loadRequests);
    if (search) search.addEventListener("input", loadRequests);
    if (status) status.addEventListener("change", loadRequests);
    if (priority) priority.addEventListener("change", loadRequests);
});

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}



async function importTelegramDestinationsFile() {
    const fileInput = document.getElementById("telegramDestinationsFile");
    const message = document.getElementById("telegramImportMessage");

    if (!fileInput || !fileInput.files.length) {
        message.textContent = "Please select a TXT or CSV file.";
        return;
    }

    const file = fileInput.files[0];

    if (file.size > 5 * 1024 * 1024) {
        message.textContent = "File is too large. Maximum size is 5 MB.";
        return;
    }

    message.textContent = "Importing...";

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch(
            "/api/v1/admin/telegram-destinations/import",
            {
                method: "POST",
                headers: {
                    "Authorization":
                        "Bearer " + localStorage.getItem("admin_access_token")
                },
                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Failed to import Telegram links."
            );
        }

        message.textContent =
            "Import completed: " +
            data.imported +
            " imported, " +
            data.skipped_existing +
            " already existed.";

        fileInput.value = "";

        await loadTelegramDestinations();

    } catch (error) {
        console.error("Telegram destination import failed:", error);
        message.textContent = error.message;
    }
}

