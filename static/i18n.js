const I18N_LANGS = ["zh", "ja", "en", "ko"];

const I18N_LANG_LABELS = {
  zh: "中文",
  ja: "日本語",
  en: "English",
  ko: "한국어",
};

const LANG_STORAGE_KEY = "aiaudio_lang";

const I18N = {
  zh: {
    "login.title": "登录 - AI AUDIO",
    "login.subtitle": "请选择登录方式",
    "login.orEmail": "或使用邮箱登录",
    "login.emailPlaceholder": "邮箱地址",
    "login.codePlaceholder": "验证码",
    "login.sendCode": "发送验证码",
    "login.emailLogin": "邮箱登录",
    "login.resendIn": "{n}s 后重发",
    "login.gmailUseGoogle": "Gmail 邮箱请点击页面上方的 Google 按钮登录",
    "login.openingGoogle": "正在打开 Google 登录，请在弹窗中完成登录...",
    "login.serviceUnavailable": "无法连接服务，请稍后重试",
    "login.configFailed": "登录配置读取失败",
    "login.noMethod": "服务端尚未配置任何登录方式",
    "login.googleFailed": "Google 登录组件加载失败，请刷新重试",
    "login.signingIn": "正在登录...",
    "login.signInFailed": "登录失败",
    "login.requestFailed": "登录请求失败，请稍后重试",
    "login.enterEmail": "请输入邮箱地址",
    "login.codeSent": "验证码已发送，请查收邮件",
    "login.sendFailed": "发送失败",
    "login.sendRequestFailed": "发送请求失败，请稍后重试",
    "login.enterEmailAndCode": "请输入邮箱和验证码",
    "app.title": "ASMR 制作 - AI AUDIO",
    "nav.asrm": "ASMR 制作",
    "nav.credits": "购买积分",
    "nav.payment": "支付",
    "nav.points": "积分",
    "nav.soon": "即将上线",
    "topbar.logout": "退出登录",
    "hero.kicker": "AI AUDIO STUDIO",
    "hero.title": "让想象，成为可听见的声音",
    "hero.desc": "挑选声线角色，写下你的灵感，AI 为你生成专属 ASMR 音频作品。从一段文字，到沉浸式声境。",
    "hero.f1": "多角色声线",
    "hero.f2": "四种语言",
    "hero.f3": "高清音质输出",
    "page.configTitle": "创作配置",
    "page.configHint": "填写作品信息，选择合适角色，提交后可在下方查询进度。",
    "form.title": "作品标题",
    "form.titlePlaceholder": "例如：雨夜治愈轻声",
    "form.characters": "参与角色",
    "form.loadingCharacters": "正在加载角色...",
    "form.noCharacters": "暂无可用角色，请先导入角色。",
    "form.moreCharacters": "角色较多，当前只显示前 {n} 个。",
    "form.loadCharactersFailed": "角色加载失败：",
    "form.theme": "创作主题",
    "form.themePlaceholder": "详细的创作主题与情节描述",
    "form.duration": "目标时长（分钟）",
    "form.language": "语言",
    "form.lang.zh": "中文 zh",
    "form.lang.ja": "日语 ja",
    "form.lang.en": "英语 en",
    "form.lang.ko": "韩语 ko",
    "form.typeBadge": "任务类型：ASMR_TEXT",
    "form.submit": "下发任务",
    "form.enterTitle": "请输入作品标题",
    "form.selectCharacter": "请至少选择一个角色",
    "form.enterTheme": "请输入创作主题",
    "form.invalidDuration": "时长必须是 1 到 60 之间的整数",
    "form.submitSuccess": "下发成功",
    "form.submitFailed": "下发失败：",
    "result.created": "任务已创建",
    "result.taskId": "任务 ID：",
    "result.status": "当前状态：",
    "result.queryBtn": "查询任务状态",
    "result.queryFailed": "查询失败：",
    "subtask.tokens": "prompt tokens: {p} · completion tokens: {c}",
    "app.userFallback": "用户 ",
  },
  ja: {
    "login.title": "ログイン - AI AUDIO",
    "login.subtitle": "ログイン方法を選択してください",
    "login.orEmail": "またはメールアドレスでログイン",
    "login.emailPlaceholder": "メールアドレス",
    "login.codePlaceholder": "認証コード",
    "login.sendCode": "認証コードを送信",
    "login.emailLogin": "メールでログイン",
    "login.resendIn": "{n}秒後に再送",
    "login.gmailUseGoogle": "Gmail アドレスは上方の Google ボタンでログインしてください",
    "login.openingGoogle": "Google ログインを開いています。ポップアップでログインを完了してください...",
    "login.serviceUnavailable": "サービスに接続できません。しばらくしてから再試行してください",
    "login.configFailed": "ログイン設定の読み込みに失敗しました",
    "login.noMethod": "サーバーにログイン方法が設定されていません",
    "login.googleFailed": "Google ログインコンポーネントの読み込みに失敗しました。更新して再試行してください",
    "login.signingIn": "ログイン中...",
    "login.signInFailed": "ログインに失敗しました",
    "login.requestFailed": "ログインリクエストが失敗しました。しばらくしてから再試行してください",
    "login.enterEmail": "メールアドレスを入力してください",
    "login.codeSent": "認証コードを送信しました。メールをご確認ください",
    "login.sendFailed": "送信に失敗しました",
    "login.sendRequestFailed": "送信リクエストが失敗しました。しばらくしてから再試行してください",
    "login.enterEmailAndCode": "メールアドレスと認証コードを入力してください",
    "app.title": "ASMR 制作 - AI AUDIO",
    "nav.asrm": "ASMR 制作",
    "nav.credits": "クレジット購入",
    "nav.payment": "お支払い",
    "nav.points": "クレジット",
    "nav.soon": "近日公開",
    "topbar.logout": "ログアウト",
    "hero.kicker": "AI AUDIO STUDIO",
    "hero.title": "想象を、聴こえる声に。",
    "hero.desc": "声のキャラクターを選び、インスピレーションを書くだけ。AI があなただけの ASMR オーディオ作品を生成します。",
    "hero.f1": "複数の声質",
    "hero.f2": "4 言語対応",
    "hero.f3": "高音質出力",
    "page.configTitle": "創作設定",
    "page.configHint": "作品情報を入力し、キャラクターを選択してください。送信後は下で進捗を確認できます。",
    "form.title": "作品タイトル",
    "form.titlePlaceholder": "例：雨の夜の癒しのささやき",
    "form.characters": "参加キャラクター",
    "form.loadingCharacters": "キャラクターを読み込み中...",
    "form.noCharacters": "利用可能なキャラクターがいません。先にインポートしてください。",
    "form.moreCharacters": "キャラクターが多く、最初の {n} 件のみ表示しています。",
    "form.loadCharactersFailed": "キャラクターの読み込みに失敗しました：",
    "form.theme": "創作テーマ",
    "form.themePlaceholder": "創作テーマとあらすじの詳細",
    "form.duration": "目標時間（分）",
    "form.language": "言語",
    "form.lang.zh": "中国語 zh",
    "form.lang.ja": "日本語 ja",
    "form.lang.en": "英語 en",
    "form.lang.ko": "韓国語 ko",
    "form.typeBadge": "タスク種類：ASMR_TEXT",
    "form.submit": "タスクを送信",
    "form.enterTitle": "作品タイトルを入力してください",
    "form.selectCharacter": "キャラクターを 1 つ以上選択してください",
    "form.enterTheme": "創作テーマを入力してください",
    "form.invalidDuration": "時間は 1 ～ 60 の整数で入力してください",
    "form.submitSuccess": "送信しました",
    "form.submitFailed": "送信に失敗しました：",
    "result.created": "タスクを作成しました",
    "result.taskId": "タスク ID：",
    "result.status": "現在の状態：",
    "result.queryBtn": "タスクの状態を確認",
    "result.queryFailed": "確認に失敗しました：",
    "subtask.tokens": "prompt tokens: {p} · completion tokens: {c}",
    "app.userFallback": "ユーザー ",
  },
  en: {
    "login.title": "Sign in - AI AUDIO",
    "login.subtitle": "Choose a sign-in method",
    "login.orEmail": "Or sign in with email",
    "login.emailPlaceholder": "Email address",
    "login.codePlaceholder": "Verification code",
    "login.sendCode": "Send code",
    "login.emailLogin": "Email sign in",
    "login.resendIn": "Resend in {n}s",
    "login.gmailUseGoogle": "For Gmail, please use the Google button above to sign in",
    "login.openingGoogle": "Opening Google sign-in, please complete it in the popup...",
    "login.serviceUnavailable": "Unable to connect to the service. Please try again later.",
    "login.configFailed": "Failed to load sign-in configuration",
    "login.noMethod": "No sign-in method is configured on the server",
    "login.googleFailed": "Failed to load Google sign-in. Please refresh and try again.",
    "login.signingIn": "Signing in...",
    "login.signInFailed": "Sign-in failed",
    "login.requestFailed": "Sign-in request failed. Please try again later.",
    "login.enterEmail": "Please enter your email address",
    "login.codeSent": "Verification code sent. Please check your email.",
    "login.sendFailed": "Send failed",
    "login.sendRequestFailed": "Send request failed. Please try again later.",
    "login.enterEmailAndCode": "Please enter your email and verification code",
    "app.title": "ASMR Studio - AI AUDIO",
    "nav.asrm": "ASMR Studio",
    "nav.credits": "Buy Credits",
    "nav.payment": "Payment",
    "nav.points": "Credits",
    "nav.soon": "Coming soon",
    "topbar.logout": "Sign out",
    "hero.kicker": "AI AUDIO STUDIO",
    "hero.title": "Turn your imagination into sound you can hear",
    "hero.desc": "Pick voice characters, write your idea, and AI creates your own ASMR audio. From a few words to an immersive soundscape.",
    "hero.f1": "Multiple voices",
    "hero.f2": "Four languages",
    "hero.f3": "HD audio output",
    "page.configTitle": "Creation Settings",
    "page.configHint": "Fill in the details, choose your characters, and track progress below after submitting.",
    "form.title": "Work title",
    "form.titlePlaceholder": "e.g. Soothing whispers on a rainy night",
    "form.characters": "Characters",
    "form.loadingCharacters": "Loading characters...",
    "form.noCharacters": "No characters available. Please import some first.",
    "form.moreCharacters": "Many characters found, showing only the first {n}.",
    "form.loadCharactersFailed": "Failed to load characters: ",
    "form.theme": "Creative theme",
    "form.themePlaceholder": "Detailed theme and storyline",
    "form.duration": "Target duration (min)",
    "form.language": "Language",
    "form.lang.zh": "Chinese zh",
    "form.lang.ja": "Japanese ja",
    "form.lang.en": "English en",
    "form.lang.ko": "Korean ko",
    "form.typeBadge": "Task type: ASMR_TEXT",
    "form.submit": "Submit task",
    "form.enterTitle": "Please enter a work title",
    "form.selectCharacter": "Please select at least one character",
    "form.enterTheme": "Please enter a creative theme",
    "form.invalidDuration": "Duration must be an integer between 1 and 60",
    "form.submitSuccess": "Submitted successfully",
    "form.submitFailed": "Submission failed: ",
    "result.created": "Task created",
    "result.taskId": "Task ID: ",
    "result.status": "Current status: ",
    "result.queryBtn": "Check task status",
    "result.queryFailed": "Check failed: ",
    "subtask.tokens": "prompt tokens: {p} · completion tokens: {c}",
    "app.userFallback": "User ",
  },
  ko: {
    "login.title": "로그인 - AI AUDIO",
    "login.subtitle": "로그인 방식을 선택하세요",
    "login.orEmail": "또는 이메일로 로그인",
    "login.emailPlaceholder": "이메일 주소",
    "login.codePlaceholder": "인증 코드",
    "login.sendCode": "인증 코드 보내기",
    "login.emailLogin": "이메일 로그인",
    "login.resendIn": "{n}초 후 재전송",
    "login.gmailUseGoogle": "Gmail 주소는 위의 Google 버튼으로 로그인하세요",
    "login.openingGoogle": "Google 로그인을 여는 중입니다. 팝업에서 로그인을 완료하세요...",
    "login.serviceUnavailable": "서비스에 연결할 수 없습니다. 나중에 다시 시도하세요.",
    "login.configFailed": "로그인 설정을 불러오지 못했습니다",
    "login.noMethod": "서버에 로그인 방식이 설정되지 않았습니다",
    "login.googleFailed": "Google 로그인 구성 요소를 불러오지 못했습니다. 새로고침 후 다시 시도하세요.",
    "login.signingIn": "로그인 중...",
    "login.signInFailed": "로그인 실패",
    "login.requestFailed": "로그인 요청이 실패했습니다. 나중에 다시 시도하세요.",
    "login.enterEmail": "이메일 주소를 입력하세요",
    "login.codeSent": "인증 코드를 보냈습니다. 이메일을 확인하세요.",
    "login.sendFailed": "전송 실패",
    "login.sendRequestFailed": "전송 요청이 실패했습니다. 나중에 다시 시도하세요.",
    "login.enterEmailAndCode": "이메일과 인증 코드를 입력하세요",
    "app.title": "ASMR 제작 - AI AUDIO",
    "nav.asrm": "ASMR 제작",
    "nav.credits": "크레딧 구매",
    "nav.payment": "결제",
    "nav.points": "크레딧",
    "nav.soon": "곧 출시",
    "topbar.logout": "로그아웃",
    "hero.kicker": "AI AUDIO STUDIO",
    "hero.title": "상상을, 들을 수 있는 소리로",
    "hero.desc": "목소리 캐릭터를 고르고 아이디어를 적으세요. AI가 당신만의 ASMR 오디오 작품을 만들어 드립니다.",
    "hero.f1": "다양한 목소리",
    "hero.f2": "4개 언어 지원",
    "hero.f3": "고음질 출력",
    "page.configTitle": "제작 설정",
    "page.configHint": "작품 정보를 입력하고 캐릭터를 선택하세요. 제출 후 아래에서 진행 상황을 확인할 수 있습니다.",
    "form.title": "작품 제목",
    "form.titlePlaceholder": "예: 비 오는 밤의 치유 속삭임",
    "form.characters": "등장 캐릭터",
    "form.loadingCharacters": "캐릭터를 불러오는 중...",
    "form.noCharacters": "사용 가능한 캐릭터가 없습니다. 먼저 가져오세요.",
    "form.moreCharacters": "캐릭터가 많아 처음 {n}개만 표시합니다.",
    "form.loadCharactersFailed": "캐릭터를 불러오지 못했습니다: ",
    "form.theme": "제작 테마",
    "form.themePlaceholder": "제작 테마와 줄거리를 자세히 적으세요",
    "form.duration": "목표 길이 (분)",
    "form.language": "언어",
    "form.lang.zh": "중국어 zh",
    "form.lang.ja": "일본어 ja",
    "form.lang.en": "영어 en",
    "form.lang.ko": "한국어 ko",
    "form.typeBadge": "작업 유형: ASMR_TEXT",
    "form.submit": "작업 제출",
    "form.enterTitle": "작품 제목을 입력하세요",
    "form.selectCharacter": "캐릭터를 하나 이상 선택하세요",
    "form.enterTheme": "제작 테마를 입력하세요",
    "form.invalidDuration": "길이는 1에서 60 사이의 정수여야 합니다",
    "form.submitSuccess": "제출 완료",
    "form.submitFailed": "제출 실패: ",
    "result.created": "작업이 생성되었습니다",
    "result.taskId": "작업 ID: ",
    "result.status": "현재 상태: ",
    "result.queryBtn": "작업 상태 확인",
    "result.queryFailed": "확인 실패: ",
    "subtask.tokens": "prompt tokens: {p} · completion tokens: {c}",
    "app.userFallback": "사용자 ",
  },
};

const I18n = {
  current: "zh",

  detect() {
    const saved = localStorage.getItem(LANG_STORAGE_KEY);
    if (I18N_LANGS.includes(saved)) {
      return saved;
    }
    return "zh";
  },

  htmlLang(lang) {
    if (lang === "zh") {
      return "zh-CN";
    }
    return lang;
  },

  t(key, vars) {
    const dict = I18N[this.current];
    const text = dict[key];
    if (text === undefined) {
      throw new Error("Missing i18n key: " + key + " in " + this.current);
    }
    if (!vars) {
      return text;
    }
    return text.replace(/\{(\w+)\}/g, (match, name) => {
      const value = vars[name];
      if (value === undefined) {
        throw new Error("Missing i18n variable: " + name + " for " + key);
      }
      return String(value);
    });
  },

  apply(root = document) {
    for (const el of root.querySelectorAll("[data-i18n]")) {
      el.textContent = this.t(el.dataset.i18n);
    }
    for (const el of root.querySelectorAll("[data-i18n-placeholder]")) {
      el.placeholder = this.t(el.dataset.i18nPlaceholder);
    }
  },

  set(lang) {
    if (!I18N_LANGS.includes(lang)) {
      throw new Error("Unsupported language: " + lang);
    }
    this.current = lang;
    localStorage.setItem(LANG_STORAGE_KEY, lang);
    document.documentElement.lang = this.htmlLang(lang);
    this.syncTitle();
    this.apply();
    window.dispatchEvent(new CustomEvent("aiaudio:langchange", { detail: { lang } }));
  },

  titleKey() {
    const title = document.querySelector("title");
    if (title) {
      return title.dataset.i18n || "";
    }
    return "";
  },

  syncTitle() {
    const key = this.titleKey();
    if (key) {
      document.title = this.t(key);
    }
  },

  buildSwitcher(container) {
    const select = document.createElement("select");
    select.className = "lang-select";
    select.setAttribute("aria-label", "Language");
    for (const lang of I18N_LANGS) {
      const option = document.createElement("option");
      option.value = lang;
      option.textContent = I18N_LANG_LABELS[lang];
      select.appendChild(option);
    }
    select.value = this.current;
    select.addEventListener("change", () => this.set(select.value));
    container.appendChild(select);
    return select;
  },

  init() {
    this.current = this.detect();
    document.documentElement.lang = this.htmlLang(this.current);
    this.syncTitle();
    this.apply();
  },
};

window.I18n = I18n;
