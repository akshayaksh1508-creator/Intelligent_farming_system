// Shared Frontend JS (Pure JS, API driven)

document.addEventListener("DOMContentLoaded", () => {
    checkAuthStatus();
    initChatbot();
    loadPublicStats();
});

async function loadPublicStats() {
    const farmersEl = document.getElementById("stat-farmers");
    if (!farmersEl) return;
    
    try {
        const res = await fetch("/api/public/stats");
        const data = await res.json();
        
        document.getElementById("stat-farmers").textContent = data.farmers;
        document.getElementById("stat-predictions").textContent = data.predictions;
        document.getElementById("stat-districts").textContent = data.districts;
    } catch (e) {
        console.error("Error loading stats:", e);
    }
}

async function checkAuthStatus() {
    try {
        const res = await fetch("/api/auth/me");
        const data = await res.json();
        const authNav = document.getElementById("nav-auth-actions");
        if (authNav) {
            if (data.authenticated) {
                let dashboardBtn = "";
                const u = data.user;
                if (u.role === "admin") {
                    dashboardBtn = `<a href="/admin" class="btn-ghost-fw"><i class="fas fa-tachometer-alt"></i> Dashboard</a>`;
                } else if (u.role === "farmer") {
                    if (u.profile_completed && u.is_approved) {
                        dashboardBtn = `<a href="/dashboard.html" class="btn-ghost-fw"><i class="fas fa-tachometer-alt"></i> Dashboard</a>`;
                    } else if (!u.profile_completed) {
                        dashboardBtn = `<a href="/profile-setup.html" class="btn-ghost-fw"><i class="fas fa-user-edit"></i> Setup Profile</a>`;
                    }
                }
                
                authNav.innerHTML = `
                    ${dashboardBtn}
                    <button onclick="logoutUser()" class="btn-outline-fw">Logout</button>
                `;
            } else {
                authNav.innerHTML = `
                    <a href="/login.html" class="btn-ghost-fw">Login</a>
                    <a href="/register.html" class="btn-primary-fw">Get Started <i class="fas fa-arrow-right"></i></a>
                `;
            }
        }
    } catch (e) {
        console.error("Auth check error:", e);
    }
}

async function logoutUser() {
    await fetch("/api/auth/logout", { method: "POST" });
    window.location.href = "/login.html";
}

function initChatbot() {
    const input = document.getElementById("chatInput");
    if (input) {
        input.addEventListener("keypress", (e) => {
            if (e.key === "Enter") sendChatMessage();
        });
    }
}

function toggleChatbot() {
    const panel = document.getElementById("chatbotPanel");
    if (panel) panel.classList.toggle("open");
}

async function sendChatMessage() {
    const input = document.getElementById("chatInput");
    const msg = input.value.trim();
    if (!msg) return;

    appendMsg(msg, "user");
    input.value = "";

    try {
        const res = await fetch("/api/chatbot/message", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: msg })
        });
        const data = await res.json();
        appendMsg(data.response, "bot");
    } catch (e) {
        appendMsg("Connection error.", "bot");
    }
}

function appendMsg(text, sender) {
    const container = document.getElementById("chatMessages");
    if (!container) return;
    const div = document.createElement("div");
    div.className = `chat-msg ${sender}`;
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}
