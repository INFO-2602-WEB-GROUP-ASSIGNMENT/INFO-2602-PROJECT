(function () {
	const API = {
		users: "/api/admin/users",
		fallbackUsers: "/api/users",
		userRoutines: (userId) => `/api/admin/users/${userId}/routines`,
		updateRoutine: (routineId) => `/api/admin/routines/${routineId}`,
		deleteRoutine: (routineId) => `/api/admin/routines/${routineId}`,
		updateUser: (userId) => `/api/admin/users/${userId}`,
		deleteUser: (userId) => `/api/admin/users/${userId}`
	};

	const state = {
		users: [],
		filteredUsers: [],
		selectedUserId: null,
		routines: [],
		editingRoutineId: null
	};

	const DAYS_OF_WEEK = [
		"Monday",
		"Tuesday",
		"Wednesday",
		"Thursday",
		"Friday",
		"Saturday",
		"Sunday"
	];

	const els = {
		refreshBtn: document.getElementById("refreshAdminDataBtn"),
		statusBanner: document.getElementById("adminStatusBanner"),
		userSearchInput: document.getElementById("userSearchInput"),
		usersTableBody: document.getElementById("usersTableBody"),
		routinesList: document.getElementById("routinesList"),
		selectedUserLabel: document.getElementById("selectedUserLabel"),
		totalUsersMetric: document.getElementById("totalUsersMetric"),
		totalAdminsMetric: document.getElementById("totalAdminsMetric"),
		totalRoutinesMetric: document.getElementById("totalRoutinesMetric"),
		editRoutineModal: document.getElementById("editRoutineModal"),
		editRoutineForm: document.getElementById("editRoutineForm"),
		editRoutineDay: document.getElementById("editRoutineDay"),
		editRoutineDescription: document.getElementById("editRoutineDescription"),
		cancelEditRoutineBtn: document.getElementById("cancelEditRoutineBtn")
	};

	function escapeHtml(value) {
		return String(value ?? "")
			.replaceAll("&", "&amp;")
			.replaceAll("<", "&lt;")
			.replaceAll(">", "&gt;")
			.replaceAll('"', "&quot;")
			.replaceAll("'", "&#39;");
	}

	function showStatus(message, kind = "info") {
		if (!els.statusBanner) return;

		els.statusBanner.classList.remove("hidden", "info", "success", "error");
		els.statusBanner.classList.add(kind);
		els.statusBanner.textContent = message;

		if (kind !== "error") {
			window.setTimeout(() => {
				els.statusBanner.classList.add("hidden");
			}, 3000);
		}
	}

	async function fetchJson(url, options = {}) {
		const response = await fetch(url, {
			headers: {
				"Content-Type": "application/json"
			},
			...options
		});

		let data = null;
		try {
			data = await response.json();
		} catch {
			data = null;
		}

		if (!response.ok) {
			const detail = data && (data.detail || data.message);
			throw new Error(detail || `Request failed (${response.status}).`);
		}

		return data;
	}

	function normalizeRole(role) {
		const value = String(role || "user").toLowerCase();
		return value === "admin" ? "admin" : "user";
	}

	function normalizeDayOfWeek(day) {
		const value = String(day || "").trim().toLowerCase();
		return DAYS_OF_WEEK.find((item) => item.toLowerCase() === value) || "";
	}

	function updateMetrics() {
		const adminCount = state.users.filter((user) => normalizeRole(user.role) === "admin").length;
		els.totalUsersMetric.textContent = String(state.users.length);
		els.totalAdminsMetric.textContent = String(adminCount);
		els.totalRoutinesMetric.textContent = String(state.routines.length);
	}

	function renderUsers() {
		const rows = state.filteredUsers;

		if (!rows.length) {
			els.usersTableBody.innerHTML = '<tr><td colspan="4" class="empty-row">No users found.</td></tr>';
			return;
		}

		els.usersTableBody.innerHTML = rows.map((user) => {
			const role = normalizeRole(user.role);
			const isSelected = Number(user.id) === Number(state.selectedUserId);

			return `
				<tr>
					<td>
						<button class="user-chip ${isSelected ? "selected" : ""}" data-select-user="${user.id}" type="button">
							<span class="user-dot"></span>
							<span>${escapeHtml(user.username || "Unknown")}</span>
						</button>
					</td>
					<td>${escapeHtml(user.email || "-")}</td>
					<td>
						<span class="role-tag ${role}">${role}</span>
					</td>
					<td>
						<div class="table-actions">
							<select class="small-select" data-role-select="${user.id}">
								<option value="user" ${role === "user" ? "selected" : ""}>user</option>
								<option value="admin" ${role === "admin" ? "selected" : ""}>admin</option>
							</select>
							<button type="button" class="small-btn" data-save-user="${user.id}">Save</button>
							<button type="button" class="danger-btn" data-delete-user="${user.id}">Delete</button>
						</div>
					</td>
				</tr>
			`;
		}).join("");
	}

	function renderRoutines() {
		if (!state.selectedUserId) {
			els.routinesList.innerHTML = '<div class="empty-box">No user selected yet.</div>';
			updateMetrics();
			return;
		}

		if (!state.routines.length) {
			els.routinesList.innerHTML = '<div class="empty-box">This user has no routines.</div>';
			updateMetrics();
			return;
		}

		els.routinesList.innerHTML = state.routines.map((routine) => {
			const day = routine.day_of_week || routine.name || "Routine";
			const description = routine.description || "No description provided.";

			return `
				<article class="routine-card">
					<div class="routine-header">
						<div>
							<p class="routine-day">${escapeHtml(day)}</p>
							<p class="routine-id">Routine #${escapeHtml(routine.id)}</p>
						</div>
						<div class="routine-actions">
							<button type="button" class="ghost-btn" data-edit-routine="${routine.id}">Edit</button>
							<button type="button" class="danger-btn" data-delete-routine="${routine.id}">Delete</button>
						</div>
					</div>
					<p class="routine-description">${escapeHtml(description)}</p>
				</article>
			`;
		}).join("");

		updateMetrics();
	}

	function applyUserFilter() {
		const query = (els.userSearchInput.value || "").trim().toLowerCase();

		if (!query) {
			state.filteredUsers = [...state.users];
		} else {
			state.filteredUsers = state.users.filter((user) => {
				const username = String(user.username || "").toLowerCase();
				const email = String(user.email || "").toLowerCase();
				return username.includes(query) || email.includes(query);
			});
		}

		renderUsers();
	}

	async function loadUsers() {
		try {
			state.users = await fetchJson(API.users);
		} catch {
			state.users = await fetchJson(API.fallbackUsers);
			showStatus("Loaded users from fallback endpoint. Add admin-specific user route when ready.", "info");
		}

		state.filteredUsers = [...state.users];
		renderUsers();
		updateMetrics();

		if (state.users.length && !state.selectedUserId) {
			await selectUser(state.users[0].id);
		}
	}

	async function loadRoutinesForUser(userId) {
		state.routines = [];
		renderRoutines();

		try {
			const data = await fetchJson(API.userRoutines(userId));
			state.routines = Array.isArray(data) ? data : [];
		} catch (error) {
			showStatus(`Could not load routines: ${error.message}`, "error");
		}

		renderRoutines();
	}

	async function selectUser(userId) {
		state.selectedUserId = Number(userId);

		const selectedUser = state.users.find((user) => Number(user.id) === Number(userId));
		if (selectedUser) {
			els.selectedUserLabel.textContent = `Routines for ${selectedUser.username}`;
		}

		renderUsers();
		await loadRoutinesForUser(userId);
	}

	function openEditRoutineModal(routine) {
		state.editingRoutineId = Number(routine.id);
		const normalizedDay = normalizeDayOfWeek(routine.day_of_week || routine.name || "");
		els.editRoutineDay.value = normalizedDay;
		els.editRoutineDescription.value = routine.description || "";
		els.editRoutineModal.classList.remove("hidden");
		els.editRoutineModal.setAttribute("aria-hidden", "false");
	}

	function closeEditRoutineModal() {
		state.editingRoutineId = null;
		els.editRoutineModal.classList.add("hidden");
		els.editRoutineModal.setAttribute("aria-hidden", "true");
		els.editRoutineForm.reset();
	}

	async function saveUserRole(userId) {
		const roleSelect = document.querySelector(`[data-role-select="${userId}"]`);
		const nextRole = roleSelect ? roleSelect.value : "user";

		await fetchJson(API.updateUser(userId), {
			method: "PATCH",
			body: JSON.stringify({ role: nextRole })
		});

		const user = state.users.find((item) => Number(item.id) === Number(userId));
		if (user) user.role = nextRole;

		applyUserFilter();
		updateMetrics();
		showStatus("User role updated.", "success");
	}

	async function removeUser(userId) {
		if (!window.confirm("Delete this user account? This action cannot be undone.")) {
			return;
		}

		await fetchJson(API.deleteUser(userId), {
			method: "DELETE"
		});

		state.users = state.users.filter((user) => Number(user.id) !== Number(userId));
		state.filteredUsers = state.filteredUsers.filter((user) => Number(user.id) !== Number(userId));

		if (Number(state.selectedUserId) === Number(userId)) {
			state.selectedUserId = null;
			state.routines = [];
			els.selectedUserLabel.textContent = "Choose a user to view their routines.";
		}

		renderUsers();
		renderRoutines();
		updateMetrics();
		showStatus("User account deleted.", "success");
	}

	async function saveRoutineChanges() {
		const day = (els.editRoutineDay.value || "").trim();
		const description = (els.editRoutineDescription.value || "").trim();

		if (!day) {
			showStatus("Routine day is required.", "error");
			return;
		}

		const payload = {
			day_of_week: day,
			description: description
		};

		await fetchJson(API.updateRoutine(state.editingRoutineId), {
			method: "PATCH",
			body: JSON.stringify(payload)
		});

		const routine = state.routines.find((item) => Number(item.id) === Number(state.editingRoutineId));
		if (routine) {
			routine.day_of_week = day;
			routine.name = day;
			routine.description = description;
		}

		renderRoutines();
		closeEditRoutineModal();
		showStatus("Routine updated successfully.", "success");
	}

	async function removeRoutine(routineId) {
		if (!window.confirm("Delete this routine?")) {
			return;
		}

		await fetchJson(API.deleteRoutine(routineId), {
			method: "DELETE"
		});

		state.routines = state.routines.filter((routine) => Number(routine.id) !== Number(routineId));
		renderRoutines();
		showStatus("Routine deleted.", "success");
	}

	function bindEvents() {
		els.refreshBtn.addEventListener("click", async () => {
			await loadUsers();
			if (state.selectedUserId) {
				await loadRoutinesForUser(state.selectedUserId);
			}
			showStatus("Admin data refreshed.", "success");
		});

		els.userSearchInput.addEventListener("input", applyUserFilter);

		els.usersTableBody.addEventListener("click", async (event) => {
			const selectButton = event.target.closest("[data-select-user]");
			if (selectButton) {
				const userId = Number(selectButton.getAttribute("data-select-user"));
				await selectUser(userId);
				return;
			}

			const saveButton = event.target.closest("[data-save-user]");
			if (saveButton) {
				const userId = Number(saveButton.getAttribute("data-save-user"));
				try {
					await saveUserRole(userId);
				} catch (error) {
					showStatus(`Could not update user: ${error.message}`, "error");
				}
				return;
			}

			const deleteButton = event.target.closest("[data-delete-user]");
			if (deleteButton) {
				const userId = Number(deleteButton.getAttribute("data-delete-user"));
				try {
					await removeUser(userId);
				} catch (error) {
					showStatus(`Could not delete user: ${error.message}`, "error");
				}
			}
		});

		els.routinesList.addEventListener("click", async (event) => {
			const editButton = event.target.closest("[data-edit-routine]");
			if (editButton) {
				const routineId = Number(editButton.getAttribute("data-edit-routine"));
				const routine = state.routines.find((item) => Number(item.id) === routineId);
				if (routine) openEditRoutineModal(routine);
				return;
			}

			const deleteButton = event.target.closest("[data-delete-routine]");
			if (deleteButton) {
				const routineId = Number(deleteButton.getAttribute("data-delete-routine"));
				try {
					await removeRoutine(routineId);
				} catch (error) {
					showStatus(`Could not delete routine: ${error.message}`, "error");
				}
			}
		});

		els.cancelEditRoutineBtn.addEventListener("click", closeEditRoutineModal);

		els.editRoutineForm.addEventListener("submit", async (event) => {
			event.preventDefault();
			try {
				await saveRoutineChanges();
			} catch (error) {
				showStatus(`Could not update routine: ${error.message}`, "error");
			}
		});
	}

	async function init() {
		bindEvents();
		try {
			await loadUsers();
		} catch (error) {
			showStatus(`Could not load users: ${error.message}`, "error");
			els.usersTableBody.innerHTML = '<tr><td colspan="4" class="empty-row">Unable to load users.</td></tr>';
		}
	}

	init();
})();
