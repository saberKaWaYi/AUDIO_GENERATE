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

  statusTag(status) {
    const tag = document.createElement("span");
    tag.className = "status-tag status-" + status;
    tag.textContent = status;
    return tag;
  },

  infoRow(label, value) {
    const row = document.createElement("div");
    row.className = "detail-meta-row";
    const key = document.createElement("span");
    key.className = "detail-meta-key";
    key.textContent = label;
    const val = document.createElement("span");
    val.className = "detail-meta-value";
    val.textContent = value;
    row.appendChild(key);
    row.appendChild(val);
    return row;
  },

  collapsible(label, count, action) {
    const wrap = document.createElement("div");
    wrap.className = "subtask-group";
    const head = document.createElement("div");
    head.className = "subtask-group-head";
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "subtask-group-toggle";
    toggle.setAttribute("aria-expanded", "false");
    const caret = document.createElement("span");
    caret.className = "subtask-group-caret";
    caret.textContent = "+";
    const text = document.createElement("span");
    text.textContent = label + "（" + count + "）";
    toggle.appendChild(caret);
    toggle.appendChild(text);
    const body = document.createElement("div");
    body.className = "subtask-group-body";
    body.hidden = true;
    toggle.addEventListener("click", () => {
      const expanded = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", expanded ? "false" : "true");
      body.hidden = expanded;
      caret.textContent = expanded ? "+" : "−";
    });
    head.appendChild(toggle);
    if (action) {
      head.appendChild(action);
    }
    wrap.appendChild(head);
    wrap.appendChild(body);
    return { root: wrap, body: body };
  },

  releaseButton(subtask, onChanged, onError) {
    if (subtask.status !== "debug") {
      return null;
    }
    const button = document.createElement("button");
    button.type = "button";
    button.className = "subtask-release";
    button.textContent = I18n.t("taskdetail.release");
    button.addEventListener("click", async () => {
      button.disabled = true;
      try {
        await this.api("/api/audio/tasks/" + encodeURIComponent(subtask.subtask_id) + "/release", { method: "POST" });
        await onChanged();
      } catch (e) {
        button.disabled = false;
        onError(e);
      }
    });
    return button;
  },

  downloadButton(workId) {
    const link = document.createElement("a");
    link.className = "subtask-download";
    link.href = "/api/audio/works/" + encodeURIComponent(workId) + "/audio";
    link.textContent = I18n.t("taskdetail.download");
    return link;
  },

  refreshButton(subtask, onChanged, onError) {
    if (subtask.status !== "success" && subtask.status !== "failed") {
      return null;
    }
    const button = document.createElement("button");
    button.type = "button";
    button.className = "subtask-refresh";
    button.textContent = I18n.t("taskdetail.refreshSubtask");
    button.addEventListener("click", async () => {
      button.disabled = true;
      try {
        await this.api("/api/audio/tasks/" + encodeURIComponent(subtask.subtask_id) + "/refresh", { method: "POST" });
        await onChanged();
      } catch (e) {
        button.disabled = false;
        onError(e);
      }
    });
    return button;
  },

  editTextButton(subtask, editorHost, onChanged, onError) {
    if (subtask.status !== "failed") {
      return null;
    }
    const button = document.createElement("button");
    button.type = "button";
    button.className = "subtask-refresh";
    button.textContent = I18n.t("taskdetail.editText");
    let editor = null;
    button.addEventListener("click", () => {
      if (editor) {
        editor.hidden = !editor.hidden;
        return;
      }
      editor = document.createElement("div");
      editor.className = "text-editor";
      const input = document.createElement("textarea");
      input.className = "text-editor-input";
      input.value = subtask.info.text;
      input.rows = 3;
      const save = document.createElement("button");
      save.type = "button";
      save.className = "text-editor-save";
      save.textContent = I18n.t("taskdetail.editTextSave");
      save.addEventListener("click", async () => {
        const text = input.value;
        if (!text.trim()) {
          onError(new Error(I18n.t("taskdetail.editTextEmpty")));
          return;
        }
        save.disabled = true;
        try {
          await this.api("/api/audio/tasks/" + encodeURIComponent(subtask.subtask_id) + "/text", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text }),
          });
          await onChanged();
        } catch (e) {
          save.disabled = false;
          onError(e);
        }
      });
      editor.appendChild(input);
      editor.appendChild(save);
      editorHost.appendChild(editor);
      input.focus();
    });
    return button;
  },

  generateAudioActions(subtaskId) {
    const wrap = document.createElement("div");
    wrap.className = "generate-actions";
    const play = document.createElement("button");
    play.type = "button";
    play.className = "subtask-play";
    play.textContent = I18n.t("taskdetail.play");
    const download = document.createElement("a");
    download.className = "subtask-download";
    download.href = "/api/audio/tasks/" + encodeURIComponent(subtaskId) + "/audio";
    download.textContent = I18n.t("taskdetail.download");
    let player = null;
    play.addEventListener("click", async () => {
      if (player && !player.paused) {
        player.pause();
        play.textContent = I18n.t("taskdetail.play");
        return;
      }
      if (!player) {
        player = document.createElement("audio");
        player.className = "generate-player";
        player.controls = true;
        player.src = "/api/audio/tasks/" + encodeURIComponent(subtaskId) + "/audio";
        player.addEventListener("ended", () => {
          play.textContent = I18n.t("taskdetail.play");
        });
        wrap.appendChild(player);
      }
      play.textContent = I18n.t("taskdetail.pause");
      try {
        await player.play();
      } catch (e) {
        play.textContent = I18n.t("taskdetail.play");
      }
    });
    wrap.appendChild(play);
    wrap.appendChild(download);
    return wrap;
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
