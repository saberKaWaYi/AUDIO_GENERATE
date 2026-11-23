const App = {
  currentUser: null,

  coverImageUrl(value) {
    if (/^https?:\/\//i.test(value)) {
      return value;
    }
    return "https://public-platform.r2.fish.audio/" + value.replace(/^\/+/, "");
  },

  voiceThumb(value, title) {
    const thumb = document.createElement("span");
    thumb.className = "voice-thumb";
    if (value) {
      const img = document.createElement("img");
      img.src = this.coverImageUrl(value);
      img.alt = "";
      thumb.appendChild(img);
    } else {
      thumb.textContent = title.slice(0, 1);
    }
    return thumb;
  },

  async api(path, options = {}) {
    const res = await fetch(path, {
      credentials: "same-origin",
      ...options,
    });
    const data = await res.json();
    if (!res.ok) {
      const error = new Error(data.detail);
      error.status = res.status;
      throw error;
    }
    return data;
  },

  async requireAuth() {
    try {
      this.currentUser = await this.api("/api/auth/me");
    } catch (e) {
      window.location.replace("/login.html");
      return false;
    }
    return true;
  },

  displayName() {
    const user = this.currentUser;
    return user.name || user.email || (I18n.t("app.userFallback") + user.user_id);
  },

  renderUserArea() {
    const nameEl = document.getElementById("userName");
    if (nameEl) {
      nameEl.textContent = this.displayName();
    }
    const avatar = document.getElementById("avatar");
    if (avatar && this.currentUser.picture) {
      avatar.src = this.currentUser.picture;
      avatar.hidden = false;
    }
    const sidebarName = document.getElementById("sidebarUserName");
    if (sidebarName) {
      sidebarName.textContent = this.displayName();
    }
  },

  bindLogout() {
    const btn = document.getElementById("logoutBtn");
    if (btn) {
      btn.addEventListener("click", async () => {
        try {
          await this.api("/api/auth/logout", { method: "POST" });
        } finally {
          window.location.replace("/login.html");
        }
      });
    }
  },

  initSidebar() {
    const toggle = document.getElementById("sidebarToggle");
    const sidebar = document.getElementById("sidebar");
    if (toggle && sidebar) {
      toggle.addEventListener("click", () => {
        sidebar.classList.toggle("collapsed");
      });
    }
  },

  async init() {
    const ok = await this.requireAuth();
    if (!ok) {
      return false;
    }
    this.renderUserArea();
    this.bindLogout();
    this.initSidebar();
    return true;
  },
};

window.App = App;
