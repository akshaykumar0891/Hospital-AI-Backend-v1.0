// State Management
let currentState = {
    activePanel: "dashboard",
    appointmentsPage: 1,
    appointmentsLimit: 10,
    doctors: [],
    syncInterval: null
};

// API Endpoints Prefix
const API_PREFIX = "/api/v1";

// DOM Elements
const DOM = {
    // Navigation & Global
    navItems: document.querySelectorAll(".nav-item"),
    panels: document.querySelectorAll(".panel"),
    pageTitle: document.getElementById("page-title"),
    liveDate: document.getElementById("live-date"),
    refreshBtn: document.getElementById("refresh-btn"),
    loadingSpinner: document.getElementById("loading-spinner"),
    
    // Stats Elements
    statToday: document.getElementById("stat-today"),
    statUpcoming: document.getElementById("stat-upcoming"),
    statCancelled: document.getElementById("stat-cancelled"),
    statDoctors: document.getElementById("stat-doctors"),
    
    // Dashboard Panel Elements
    recentTableBody: document.querySelector("#recent-table tbody"),
    recentEmpty: document.getElementById("recent-empty"),
    viewAllApptsBtn: document.getElementById("view-all-appts-btn"),
    
    // Appointments Panel Elements
    appointmentsTableBody: document.querySelector("#appointments-table tbody"),
    appointmentsEmpty: document.getElementById("appointments-empty"),
    searchInput: document.getElementById("search-input"),
    filterDoctor: document.getElementById("filter-doctor"),
    filterDate: document.getElementById("filter-date"),
    filterStatus: document.getElementById("filter-status"),
    resetFiltersBtn: document.getElementById("reset-filters-btn"),
    prevPageBtn: document.getElementById("prev-page-btn"),
    nextPageBtn: document.getElementById("next-page-btn"),
    pageIndicator: document.getElementById("page-indicator"),
    
    // Doctors Panel Elements
    doctorsCardsGrid: document.getElementById("doctors-cards-grid"),
    
    // Settings Panel Elements
    settingHospitalName: document.getElementById("setting-hospital-name"),
    settingTimezone: document.getElementById("setting-timezone"),
    settingDuration: document.getElementById("setting-duration"),
    settingDepartments: document.getElementById("setting-departments"),
    settingFeatures: document.getElementById("setting-features"),
    
    // Detail Modal Elements
    detailModal: document.getElementById("detail-modal"),
    closeModalBtn: document.getElementById("close-modal-btn"),
    detId: document.getElementById("det-id"),
    detStatus: document.getElementById("det-status"),
    detPatient: document.getElementById("det-patient"),
    detMobile: document.getElementById("det-mobile"),
    detDoctor: document.getElementById("det-doctor"),
    detDept: document.getElementById("det-dept"),
    detDate: document.getElementById("det-date"),
    detTime: document.getElementById("det-time"),
    detCreated: document.getElementById("det-created"),
    detUpdated: document.getElementById("det-updated"),
    detCancelled: document.getElementById("det-cancelled")
};

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
    updateLiveDate();
    setupEventListeners();
    loadAllData();
    startAutoRefresh();
});

// Update Live Date display in header
function updateLiveDate() {
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    DOM.liveDate.textContent = new Date().toLocaleDateString('en-US', options);
}

// Show/Hide Global Spinner
function showSpinner() {
    DOM.loadingSpinner.classList.remove("hidden");
}
function hideSpinner() {
    DOM.loadingSpinner.classList.add("hidden");
}

// Start Auto Refresh Loop (Every 30 seconds)
function startAutoRefresh() {
    if (currentState.syncInterval) {
        clearInterval(currentState.syncInterval);
    }
    currentState.syncInterval = setInterval(() => {
        logger("Auto refreshing dashboard state...");
        loadAllData(false); // Silent refresh (no loading spinner overlay)
    }, 30000);
}

// Debug logs
function logger(msg, data = "") {
    console.log(`[Dashboard] ${msg}`, data);
}

// Initial/Force Load Operations
async function loadAllData(displayLoading = true) {
    if (displayLoading) showSpinner();
    try {
        await Promise.all([
            fetchStats(),
            fetchDoctorsList(),
            fetchRecentAppointments(),
            fetchAppointments(),
            fetchAiCapabilities()
        ]);
    } catch (err) {
        console.error("Error loading panel data:", err);
    } finally {
        if (displayLoading) hideSpinner();
    }
}

// ----------------------------------------------------
// API REQUEST CHANNELS
// ----------------------------------------------------

// 1. Fetch Stats Cards Counts
async function fetchStats() {
    try {
        const res = await fetch(`${API_PREFIX}/dashboard/stats`);
        const json = await res.json();
        if (json.success) {
            const data = json.data;
            DOM.statToday.textContent = data.today_appointments;
            DOM.statUpcoming.textContent = data.upcoming_appointments;
            DOM.statCancelled.textContent = data.cancelled_appointments;
            DOM.statDoctors.textContent = data.total_doctors;
        }
    } catch (err) {
        logger("Failed to load dashboard statistics cards counters.", err);
    }
}

// 2. Fetch Doctors List (for filter dropdown & doctors grid)
async function fetchDoctorsList() {
    try {
        const res = await fetch(`${API_PREFIX}/dashboard/doctors`);
        const json = await res.json();
        if (json.success) {
            currentState.doctors = json.data;
            populateDoctorFilters(json.data);
            renderDoctorsGrid(json.data);
        }
    } catch (err) {
        logger("Failed to load doctors list.", err);
    }
}

// Populate Doctors Filter dropdown list
function populateDoctorFilters(doctors) {
    // Keep initial option
    DOM.filterDoctor.innerHTML = '<option value="">All Doctors</option>';
    doctors.forEach(doc => {
        const opt = document.createElement("option");
        opt.value = doc.doctor_id;
        opt.textContent = doc.doctor_name;
        DOM.filterDoctor.appendChild(opt);
    });
}

// Render Doctors Cards Grid
function renderDoctorsGrid(doctors) {
    DOM.doctorsCardsGrid.innerHTML = "";
    if (doctors.length === 0) {
        DOM.doctorsCardsGrid.innerHTML = '<div class="empty-state"><i class="fa-solid fa-user-doctor"></i><p>No active doctor profiles on call</p></div>';
        return;
    }

    doctors.forEach(doc => {
        const card = document.createElement("div");
        card.className = "doctor-card";
        card.innerHTML = `
            <div class="doctor-card-header">
                <div class="doctor-avatar">
                    <i class="fa-solid fa-stethoscope"></i>
                </div>
                <div class="doctor-title">
                    <h3>${doc.doctor_name}</h3>
                    <span>${doc.department}</span>
                </div>
            </div>
            <div class="doctor-schedule-list">
                <div class="schedule-item">
                    <span class="schedule-label">Doctor ID</span>
                    <span class="schedule-val">${doc.doctor_id}</span>
                </div>
                <div class="schedule-item">
                    <span class="schedule-label">Timings</span>
                    <span class="schedule-val">${doc.start_time} - ${doc.end_time}</span>
                </div>
                <div class="schedule-item">
                    <span class="schedule-label">Working Days</span>
                    <span class="schedule-val">${doc.available_days}</span>
                </div>
            </div>
        `;
        DOM.doctorsCardsGrid.appendChild(card);
    });
}

// 3. Fetch Recent Appointments list
async function fetchRecentAppointments() {
    try {
        const res = await fetch(`${API_PREFIX}/dashboard/recent`);
        const json = await res.json();
        if (json.success) {
            renderRecentTable(json.data);
        }
    } catch (err) {
        logger("Failed to load recent appointments list.", err);
    }
}

function renderRecentTable(appointments) {
    DOM.recentTableBody.innerHTML = "";
    if (appointments.length === 0) {
        DOM.recentEmpty.classList.remove("hidden");
        return;
    }
    DOM.recentEmpty.classList.add("hidden");

    appointments.forEach(appt => {
        const row = document.createElement("tr");
        row.style.cursor = "pointer";
        row.addEventListener("click", () => showAppointmentDetail(appt.appointment_id));
        
        row.innerHTML = `
            <td><strong>#${appt.appointment_id}</strong></td>
            <td>${appt.patient_name}</td>
            <td>${appt.mobile}</td>
            <td>${appt.doctor_name}</td>
            <td>${appt.department}</td>
            <td>${appt.appointment_date}</td>
            <td>${appt.appointment_time}</td>
            <td><span class="badge ${getStatusBadgeClass(appt.status)}">${appt.status}</span></td>
        `;
        DOM.recentTableBody.appendChild(row);
    });
}

// Get standard CSS badge classes for statuses
function getStatusBadgeClass(status) {
    const s = status.toLowerCase();
    if (s === "booked") return "badge-booked";
    if (s === "cancelled") return "badge-cancelled";
    if (s === "rescheduled") return "badge-rescheduled";
    return "badge-completed";
}

// 4. Fetch Paginated & Filtered Appointments List
async function fetchAppointments() {
    const page = currentState.appointmentsPage;
    const limit = currentState.appointmentsLimit;
    const search = DOM.searchInput.value.trim();
    const doctorId = DOM.filterDoctor.value;
    const date = DOM.filterDate.value;
    const status = DOM.filterStatus.value;

    let url = `${API_PREFIX}/dashboard/appointments?page=${page}&limit=${limit}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (doctorId) url += `&doctor_id=${encodeURIComponent(doctorId)}`;
    if (date) url += `&date=${encodeURIComponent(date)}`;
    if (status) url += `&status=${encodeURIComponent(status)}`;

    try {
        const res = await fetch(url);
        const json = await res.json();
        if (json.success) {
            renderAppointmentsTable(json.data.appointments);
            updatePaginationControls(json.data);
        }
    } catch (err) {
        logger("Failed to query appointments list.", err);
    }
}

function renderAppointmentsTable(appointments) {
    DOM.appointmentsTableBody.innerHTML = "";
    if (appointments.length === 0) {
        DOM.appointmentsEmpty.classList.remove("hidden");
        DOM.prevPageBtn.disabled = true;
        DOM.nextPageBtn.disabled = true;
        DOM.pageIndicator.textContent = "Page 1 of 1";
        return;
    }
    DOM.appointmentsEmpty.classList.add("hidden");

    appointments.forEach(appt => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td><strong>#${appt.appointment_id}</strong></td>
            <td>${appt.patient_name}</td>
            <td>${appt.mobile}</td>
            <td>${appt.doctor_name}</td>
            <td>${appt.department}</td>
            <td>${appt.appointment_date}</td>
            <td>${appt.appointment_time}</td>
            <td><span class="badge ${getStatusBadgeClass(appt.status)}">${appt.status}</span></td>
            <td>
                <button class="action-icon-btn" onclick="showAppointmentDetail('${appt.appointment_id}')" title="View details">
                    <i class="fa-solid fa-eye"></i>
                </button>
            </td>
        `;
        DOM.appointmentsTableBody.appendChild(row);
    });
}

function updatePaginationControls(pageData) {
    const page = pageData.page;
    const totalPages = pageData.total_pages;

    DOM.pageIndicator.textContent = `Page ${page} of ${totalPages || 1}`;
    DOM.prevPageBtn.disabled = page <= 1;
    DOM.nextPageBtn.disabled = page >= totalPages;
}

// 5. Fetch and Populate AI Capabilities metadata
async function fetchAiCapabilities() {
    try {
        const res = await fetch(`${API_PREFIX}/ai-capabilities`);
        const json = await res.json();
        if (json.success) {
            const data = json.data;
            DOM.settingHospitalName.textContent = data.hospital_name || "-";
            DOM.settingTimezone.textContent = data.timezone || "-";
            DOM.settingDuration.textContent = `${data.appointment_duration_minutes} minutes` || "-";
            DOM.settingDepartments.textContent = data.available_departments ? data.available_departments.join(", ") : "-";
            
            // Render features list tags
            DOM.settingFeatures.innerHTML = "";
            if (data.supported_features) {
                data.supported_features.forEach(feat => {
                    const tag = document.createElement("span");
                    tag.className = "feature-tag";
                    tag.textContent = feat.replace(/_/g, " ");
                    DOM.settingFeatures.appendChild(tag);
                });
            }
        }
    } catch (err) {
        logger("Failed to load AI system capabilities.", err);
    }
}

// 6. Fetch Single Appointment details deep-dive
async function showAppointmentDetail(appointmentId) {
    showSpinner();
    try {
        const res = await fetch(`${API_PREFIX}/dashboard/appointment/${appointmentId}`);
        const json = await res.json();
        if (json.success) {
            populateDetailModal(json.data);
            DOM.detailModal.classList.remove("hidden");
        } else {
            alert(`Error: ${json.message}`);
        }
    } catch (err) {
        console.error("Failed to load appointment details:", err);
        alert("Failed to load appointment record. Please try again.");
    } finally {
        hideSpinner();
    }
}

function populateDetailModal(data) {
    DOM.detId.textContent = `#${data.appointment_id}`;
    
    // Status badge inside modal
    DOM.detStatus.innerHTML = `<span class="badge ${getStatusBadgeClass(data.status)}">${data.status}</span>`;
    
    DOM.detPatient.textContent = data.patient_name;
    DOM.detMobile.textContent = data.mobile;
    DOM.detDoctor.textContent = data.doctor_name;
    DOM.detDept.textContent = data.department;
    DOM.detDate.textContent = data.appointment_date;
    DOM.detTime.textContent = data.appointment_time;
    
    DOM.detCreated.textContent = data.created_at || "-";
    DOM.detUpdated.textContent = data.updated_at || "-";
    DOM.detCancelled.textContent = data.cancelled_at || "-";
}

// Close detail modal
function closeDetailModal() {
    DOM.detailModal.classList.add("hidden");
}

// ----------------------------------------------------
// SIDEBAR EVENT LISTENERS & FILTER TRIGGERS
// ----------------------------------------------------

function setupEventListeners() {
    // Sidebar Panel Toggle Items
    DOM.navItems.forEach(item => {
        item.addEventListener("click", () => {
            // Remove active style from other navigation options
            DOM.navItems.forEach(n => n.classList.remove("active"));
            item.classList.add("active");

            // Toggle panels display
            const targetPanel = item.getAttribute("data-target");
            DOM.panels.forEach(p => p.classList.remove("active"));
            document.getElementById(`panel-${targetPanel}`).classList.add("active");

            // Update Header title
            currentState.activePanel = targetPanel;
            DOM.pageTitle.textContent = getPanelTitle(targetPanel);
            
            // Reload filters and search parameters if moving back to panels
            if (targetPanel === "appointments") {
                fetchAppointments();
            } else if (targetPanel === "dashboard") {
                fetchRecentAppointments();
            }
        });
    });

    // Header force refresh btn
    DOM.refreshBtn.addEventListener("click", () => loadAllData(true));

    // Dashboard panel view-all btn
    DOM.viewAllApptsBtn.addEventListener("click", () => {
        // Trigger navigation to appointments tab
        const apptsTabItem = document.querySelector('[data-target="appointments"]');
        if (apptsTabItem) apptsTabItem.click();
    });

    // Close Modal triggers
    DOM.closeModalBtn.addEventListener("click", closeDetailModal);
    DOM.detailModal.addEventListener("click", (e) => {
        if (e.target === DOM.detailModal) {
            closeDetailModal();
        }
    });

    // Reset Filters button
    DOM.resetFiltersBtn.addEventListener("click", () => {
        DOM.searchInput.value = "";
        DOM.filterDoctor.value = "";
        DOM.filterDate.value = "";
        DOM.filterStatus.value = "";
        currentState.appointmentsPage = 1;
        fetchAppointments();
    });

    // Filter event listeners (trigger instant search query)
    DOM.searchInput.addEventListener("input", debounce(() => {
        currentState.appointmentsPage = 1;
        fetchAppointments();
    }, 300));

    DOM.filterDoctor.addEventListener("change", () => {
        currentState.appointmentsPage = 1;
        fetchAppointments();
    });

    DOM.filterDate.addEventListener("change", () => {
        currentState.appointmentsPage = 1;
        fetchAppointments();
    });

    DOM.filterStatus.addEventListener("change", () => {
        currentState.appointmentsPage = 1;
        fetchAppointments();
    });

    // Pagination Click events
    DOM.prevPageBtn.addEventListener("click", () => {
        if (currentState.appointmentsPage > 1) {
            currentState.appointmentsPage--;
            fetchAppointments();
        }
    });

    DOM.nextPageBtn.addEventListener("click", () => {
        currentState.appointmentsPage++;
        fetchAppointments();
    });
}

// Get page titles mapping
function getPanelTitle(panelName) {
    if (panelName === "dashboard") return "Dashboard Overview";
    if (panelName === "appointments") return "Appointments Manager";
    if (panelName === "doctors") return "Doctors Schedule Directory";
    return "AI Hospital Specifications Settings";
}

// Helper: Debounce search queries
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Register global helper on window so dynamic table clicks resolve correctly
window.showAppointmentDetail = showAppointmentDetail;
