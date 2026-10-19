/**
 * WayFinder Design Generator Figma Plugin (W-22)
 * Automatically draws the complete Design System, Components, and Screens
 * directly onto the Figma canvas using the native Figma Plugin API.
 */

(async () => {
  // 1. Color Palette Tokens
  const C = {
    bg: { r: 1, g: 1, b: 1 },
    bgSubtle: { r: 0.965, g: 0.973, b: 0.980 },
    surface: { r: 1, g: 1, b: 1 },
    border: { r: 0.867, g: 0.886, b: 0.910 },
    borderInput: { r: 0.537, g: 0.580, b: 0.627 },
    text: { r: 0.071, g: 0.086, b: 0.106 },
    textMuted: { r: 0.357, g: 0.400, b: 0.451 },
    brand: { r: 0.161, g: 0.663, b: 1.0 },       // #29A9FF
    brandTint: { r: 0.918, g: 0.965, b: 1.0 },   // #EAF6FF
    primary: { r: 0.039, g: 0.416, b: 0.702 },   // #0A6AB3
    accent: { r: 0.996, g: 0.729, b: 0.310 },    // #FEBA4F
    accentTint: { r: 1.0, g: 0.957, b: 0.875 },  // #FFF4DF
    accentText: { r: 0.541, g: 0.310, b: 0.059 },// #8A4F0F
    success: { r: 0.078, g: 0.424, b: 0.231 },   // #146C3B
    successTint: { r: 0.910, g: 0.965, b: 0.933 },
    danger: { r: 0.690, g: 0.184, b: 0.184 },    // #B02F2F
    dangerTint: { r: 0.992, g: 0.925, b: 0.925 },
    white: { r: 1, g: 1, b: 1 },
  };

  // 2. Safe Font Loading (Be Vietnam Pro or Inter fallback)
  let FONT_REG = { family: "Inter", style: "Regular" };
  let FONT_BOLD = { family: "Inter", style: "Bold" };
  let FONT_SEMI = { family: "Inter", style: "Semi Bold" };

  try {
    await figma.loadFontAsync({ family: "Be Vietnam Pro", style: "Regular" });
    await figma.loadFontAsync({ family: "Be Vietnam Pro", style: "Bold" });
    await figma.loadFontAsync({ family: "Be Vietnam Pro", style: "SemiBold" });
    FONT_REG = { family: "Be Vietnam Pro", style: "Regular" };
    FONT_BOLD = { family: "Be Vietnam Pro", style: "Bold" };
    FONT_SEMI = { family: "Be Vietnam Pro", style: "SemiBold" };
  } catch (e) {
    try {
      await figma.loadFontAsync({ family: "Inter", style: "Regular" });
      await figma.loadFontAsync({ family: "Inter", style: "Bold" });
      await figma.loadFontAsync({ family: "Inter", style: "Semi Bold" });
    } catch (e2) {
      await figma.loadFontAsync({ family: "Roboto", style: "Regular" });
      FONT_REG = { family: "Roboto", style: "Regular" };
      FONT_BOLD = { family: "Roboto", style: "Bold" };
      FONT_SEMI = { family: "Roboto", style: "Medium" };
    }
  }

  // 2b. Native Figma Variables Setup (Tokens Collection)
  if (figma.variables && typeof figma.variables.createVariableCollection === "function") {
    try {
      const collections = figma.variables.getLocalVariableCollections();
      let collection = collections.find(c => c.name === "WayFinder Tokens");
      if (!collection) {
        collection = figma.variables.createVariableCollection("WayFinder Tokens");
      }
      const lightModeId = collection.modes[0].modeId;
      collection.renameMode(lightModeId, "Light");
      let darkModeId;
      if (collection.modes.length > 1) {
        darkModeId = collection.modes[1].modeId;
      } else {
        darkModeId = collection.addMode("Dark");
      }

      const colorDefs = [
        { name: "color/primary", light: { r: 0.039, g: 0.416, b: 0.702 }, dark: { r: 0.161, g: 0.663, b: 1.0 } },
        { name: "color/primary-text", light: { r: 1, g: 1, b: 1 }, dark: { r: 0.055, g: 0.071, b: 0.090 } },
        { name: "color/brand", light: { r: 0.161, g: 0.663, b: 1.0 }, dark: { r: 0.161, g: 0.663, b: 1.0 } },
        { name: "color/bg", light: { r: 1, g: 1, b: 1 }, dark: { r: 0.059, g: 0.090, b: 0.165 } },
        { name: "color/surface", light: { r: 1, g: 1, b: 1 }, dark: { r: 0.118, g: 0.161, b: 0.231 } },
        { name: "color/text", light: { r: 0.071, g: 0.086, b: 0.106 }, dark: { r: 0.945, g: 0.961, b: 0.976 } },
        { name: "color/text-muted", light: { r: 0.357, g: 0.400, b: 0.451 }, dark: { r: 0.580, g: 0.639, b: 0.722 } },
        { name: "color/accent", light: { r: 0.996, g: 0.729, b: 0.310 }, dark: { r: 0.996, g: 0.729, b: 0.310 } },
        { name: "color/success", light: { r: 0.078, g: 0.424, b: 0.231 }, dark: { r: 0.298, g: 0.686, b: 0.314 } },
        { name: "color/danger", light: { r: 0.690, g: 0.184, b: 0.184 }, dark: { r: 0.937, g: 0.267, b: 0.267 } }
      ];

      for (const c of colorDefs) {
        const v = figma.variables.createVariable(c.name, collection, "COLOR");
        v.setValueForMode(lightModeId, c.light);
        v.setValueForMode(darkModeId, c.dark);
      }

      const spacingDefs = [
        { name: "spacing/space-1", val: 4 },
        { name: "spacing/space-2", val: 8 },
        { name: "spacing/space-3", val: 12 },
        { name: "spacing/space-4", val: 16 },
        { name: "spacing/space-5", val: 20 },
        { name: "spacing/space-6", val: 24 },
        { name: "spacing/space-8", val: 32 },
        { name: "spacing/space-10", val: 40 },
        { name: "spacing/space-12", val: 48 },
        { name: "spacing/space-16", val: 64 }
      ];
      for (const s of spacingDefs) {
        const v = figma.variables.createVariable(s.name, collection, "FLOAT");
        v.setValueForMode(lightModeId, s.val);
        v.setValueForMode(darkModeId, s.val);
      }
    } catch (varErr) {
      console.log("Figma Variables notice:", varErr);
    }
  }

  // Helper creators
  function createText(chars, fontSize = 16, font = FONT_REG, color = C.text) {
    const t = figma.createText();
    t.fontName = font;
    t.fontSize = fontSize;
    t.characters = chars;
    t.fills = [{ type: "SOLID", color: color }];
    return t;
  }

  function solidFill(color, opacity = 1) {
    return [{ type: "SOLID", color: color, opacity: opacity }];
  }

  function solidStroke(color, weight = 1) {
    return {
      strokes: [{ type: "SOLID", color: color }],
      strokeWeight: weight,
      strokeAlign: "INSIDE"
    };
  }

  const createdNodes = [];

  // ==========================================
  // 1. FRAME: FOUNDATIONS & COLOR TOKENS
  // ==========================================
  const tokensFrame = figma.createFrame();
  tokensFrame.name = "1. Nền tảng (Foundations & Color Tokens)";
  tokensFrame.x = 0;
  tokensFrame.y = 0;
  tokensFrame.resize(900, 500);
  tokensFrame.fills = solidFill(C.surface);
  tokensFrame.cornerRadius = 16;
  tokensFrame.strokes = [{ type: "SOLID", color: C.border }];
  tokensFrame.strokeWeight = 1;
  tokensFrame.layoutMode = "VERTICAL";
  tokensFrame.paddingTop = 32;
  tokensFrame.paddingBottom = 32;
  tokensFrame.paddingLeft = 32;
  tokensFrame.paddingRight = 32;
  tokensFrame.itemSpacing = 20;

  const tokenTitle = createText("WayFinder — Hệ màu & Tokens (W-22)", 24, FONT_BOLD, C.text);
  tokensFrame.appendChild(tokenTitle);

  const swatchesRow = figma.createFrame();
  swatchesRow.layoutMode = "HORIZONTAL";
  swatchesRow.itemSpacing = 16;
  swatchesRow.fills = [];

  const tokenList = [
    { name: "Primary", hex: "#0A6AB3", c: C.primary, note: "Link/Button (5.64:1)" },
    { name: "Brand Blue", hex: "#29A9FF", c: C.brand, note: "Minh hoạ/Tiến độ" },
    { name: "Accent Amber", hex: "#FEBA4F", c: C.accent, note: "Tiếp theo/Huy hiệu" },
    { name: "Success Green", hex: "#146C3B", c: C.success, note: "Đã học/Đúng" },
    { name: "Danger Red", hex: "#B02F2F", c: C.danger, note: "Lỗi/Sai" },
    { name: "Text Main", hex: "#12161B", c: C.text, note: "Chữ chính (18.16:1)" }
  ];

  for (const item of tokenList) {
    const box = figma.createFrame();
    box.layoutMode = "VERTICAL";
    box.itemSpacing = 6;
    box.resize(120, 130);
    box.cornerRadius = 10;
    box.fills = solidFill(C.bgSubtle);
    box.paddingTop = 10;
    box.paddingBottom = 10;
    box.paddingLeft = 10;
    box.paddingRight = 10;

    const colorCircle = figma.createFrame();
    colorCircle.resize(40, 40);
    colorCircle.cornerRadius = 20;
    colorCircle.fills = solidFill(item.c);
    box.appendChild(colorCircle);

    box.appendChild(createText(item.name, 13, FONT_SEMI, C.text));
    box.appendChild(createText(item.hex, 11, FONT_REG, C.textMuted));
    box.appendChild(createText(item.note, 10, FONT_REG, C.textMuted));

    swatchesRow.appendChild(box);
  }
  tokensFrame.appendChild(swatchesRow);
  figma.currentPage.appendChild(tokensFrame);
  createdNodes.push(tokensFrame);

  // ==========================================
  // 2. FRAME: COMPONENT LIBRARY
  // ==========================================
  const compFrame = figma.createFrame();
  compFrame.name = "2. Thư viện thành phần (Components)";
  compFrame.x = 940;
  compFrame.y = 0;
  compFrame.resize(900, 500);
  compFrame.fills = solidFill(C.surface);
  compFrame.cornerRadius = 16;
  compFrame.strokes = [{ type: "SOLID", color: C.border }];
  compFrame.strokeWeight = 1;
  compFrame.layoutMode = "VERTICAL";
  compFrame.paddingTop = 32;
  compFrame.paddingBottom = 32;
  compFrame.paddingLeft = 32;
  compFrame.paddingRight = 32;
  compFrame.itemSpacing = 20;

  compFrame.appendChild(createText("Thư viện thành phần giao diện (UI Library)", 24, FONT_BOLD, C.text));

  // Buttons Row
  const btnRow = figma.createFrame();
  btnRow.layoutMode = "HORIZONTAL";
  btnRow.itemSpacing = 12;
  btnRow.fills = [];

  function makeButton(label, bg, textColor, borderC = null) {
    const btn = figma.createFrame();
    btn.layoutMode = "HORIZONTAL";
    btn.primaryAxisAlignItems = "CENTER";
    btn.counterAxisAlignItems = "CENTER";
    btn.paddingLeft = 16;
    btn.paddingRight = 16;
    btn.paddingTop = 10;
    btn.paddingBottom = 10;
    btn.cornerRadius = 10;
    btn.fills = solidFill(bg);
    if (borderC) {
      btn.strokes = [{ type: "SOLID", color: borderC }];
      btn.strokeWeight = 1;
    }
    btn.appendChild(createText(label, 14, FONT_SEMI, textColor));
    return btn;
  }

  btnRow.appendChild(makeButton("Nút chính (44px)", C.primary, C.white));
  btnRow.appendChild(makeButton("Nút phụ", C.surface, C.text, C.borderInput));
  btnRow.appendChild(makeButton("Nút nguy hiểm", C.danger, C.white));
  btnRow.appendChild(makeButton("Nút chữ", C.brandTint, C.primary));
  compFrame.appendChild(btnRow);

  // Badges Row
  const badgeRow = figma.createFrame();
  badgeRow.layoutMode = "HORIZONTAL";
  badgeRow.itemSpacing = 8;
  badgeRow.fills = [];

  function makeBadge(label, bg, textColor) {
    const b = figma.createFrame();
    b.layoutMode = "HORIZONTAL";
    b.paddingLeft = 8;
    b.paddingRight = 8;
    b.paddingTop = 3;
    b.paddingBottom = 3;
    b.cornerRadius = 6;
    b.fills = solidFill(bg);
    b.appendChild(createText(label, 11, FONT_SEMI, textColor));
    return b;
  }

  badgeRow.appendChild(makeBadge("✓ Đã học", C.successTint, C.success));
  badgeRow.appendChild(makeBadge("Chưa học", C.bgSubtle, C.textMuted));
  badgeRow.appendChild(makeBadge("Module 3", C.accentTint, C.accentText));
  badgeRow.appendChild(makeBadge("Tạo ở đây", C.brandTint, C.primary));
  badgeRow.appendChild(makeBadge("Ngoài sách", C.bgSubtle, C.textMuted));
  compFrame.appendChild(badgeRow);

  figma.currentPage.appendChild(compFrame);
  createdNodes.push(compFrame);

  // ==========================================
  // 3. FRAME: DESKTOP ROADMAP SCREEN (1280px)
  // ==========================================
  const desktopRoadmap = figma.createFrame();
  desktopRoadmap.name = "3. Màn hình: Trang Lộ trình (/khoa-hoc/:cid) — Desktop 1280px";
  desktopRoadmap.x = 0;
  desktopRoadmap.y = 540;
  desktopRoadmap.resize(1280, 800);
  desktopRoadmap.fills = solidFill(C.bg);
  desktopRoadmap.cornerRadius = 16;
  desktopRoadmap.strokes = [{ type: "SOLID", color: C.border }];
  desktopRoadmap.strokeWeight = 1;
  desktopRoadmap.clipsContent = true;

  // Header 64px
  const header = figma.createFrame();
  header.resize(1280, 64);
  header.fills = solidFill(C.surface);
  header.strokes = [{ type: "SOLID", color: C.border }];
  header.strokeWeight = 1;
  header.layoutMode = "HORIZONTAL";
  header.primaryAxisAlignItems = "SPACE_BETWEEN";
  header.counterAxisAlignItems = "CENTER";
  header.paddingLeft = 32;
  header.paddingRight = 32;

  const headerLeft = figma.createFrame();
  headerLeft.layoutMode = "HORIZONTAL";
  headerLeft.itemSpacing = 12;
  headerLeft.counterAxisAlignItems = "CENTER";
  headerLeft.fills = [];
  headerLeft.appendChild(createText("WayFinder", 20, FONT_BOLD, C.primary));
  headerLeft.appendChild(createText("/", 16, FONT_REG, C.textMuted));
  headerLeft.appendChild(createText("Nhập môn Machine Learning", 16, FONT_SEMI, C.text));
  header.appendChild(headerLeft);

  const headerRight = figma.createFrame();
  headerRight.layoutMode = "HORIZONTAL";
  headerRight.itemSpacing = 12;
  headerRight.counterAxisAlignItems = "CENTER";
  headerRight.fills = [];
  headerRight.appendChild(makeButton("+ Tải giáo trình", C.primary, C.white));
  headerRight.appendChild(createText("Thành Ngô ▾", 14, FONT_SEMI, C.text));
  header.appendChild(headerRight);
  desktopRoadmap.appendChild(header);

  // Main Container: 2 Columns (Main Roadmap 900px + Chat 380px)
  const bodyLayout = figma.createFrame();
  bodyLayout.y = 64;
  bodyLayout.resize(1280, 736);
  bodyLayout.layoutMode = "HORIZONTAL";
  bodyLayout.fills = [];

  // Main Roadmap Col
  const roadmapMain = figma.createFrame();
  roadmapMain.resize(900, 736);
  roadmapMain.layoutMode = "VERTICAL";
  roadmapMain.paddingLeft = 32;
  roadmapMain.paddingRight = 32;
  roadmapMain.paddingTop = 32;
  roadmapMain.itemSpacing = 20;
  roadmapMain.fills = solidFill(C.bg);

  const titleRow = figma.createFrame();
  titleRow.layoutMode = "HORIZONTAL";
  titleRow.primaryAxisAlignItems = "SPACE_BETWEEN";
  titleRow.counterAxisAlignItems = "CENTER";
  titleRow.resize(836, 60);
  titleRow.fills = [];

  const titleCol = figma.createFrame();
  titleCol.layoutMode = "VERTICAL";
  titleCol.itemSpacing = 4;
  titleCol.fills = [];
  titleCol.appendChild(createText("Lộ trình học tập", 28, FONT_BOLD, C.text));
  titleCol.appendChild(createText("8 module · Xong 12/40 khái niệm", 14, FONT_REG, C.textMuted));
  titleRow.appendChild(titleCol);

  const actButtons = figma.createFrame();
  actButtons.layoutMode = "HORIZONTAL";
  actButtons.itemSpacing = 8;
  actButtons.fills = [];
  actButtons.appendChild(makeButton("Làm quiz cả khoá", C.surface, C.text, C.borderInput));
  actButtons.appendChild(makeButton("Tạo tài liệu", C.surface, C.text, C.borderInput));
  titleRow.appendChild(actButtons);
  roadmapMain.appendChild(titleRow);

  // Module 1 Card
  const m1 = figma.createFrame();
  m1.resize(836, 70);
  m1.cornerRadius = 14;
  m1.fills = solidFill(C.surface);
  m1.strokes = [{ type: "SOLID", color: C.border }];
  m1.strokeWeight = 1;
  m1.layoutMode = "HORIZONTAL";
  m1.primaryAxisAlignItems = "SPACE_BETWEEN";
  m1.counterAxisAlignItems = "CENTER";
  m1.paddingLeft = 20;
  m1.paddingRight = 20;
  m1.appendChild(createText("① Đại số tuyến tính căn bản", 18, FONT_SEMI, C.text));
  m1.appendChild(makeBadge("✓ Hoàn thành (5/5)", C.successTint, C.success));
  roadmapMain.appendChild(m1);

  // Module 2 Card (Active)
  const m2 = figma.createFrame();
  m2.resize(836, 120);
  m2.cornerRadius = 14;
  m2.fills = solidFill(C.surface);
  m2.strokes = [{ type: "SOLID", color: C.primary }];
  m2.strokeWeight = 2;
  m2.layoutMode = "VERTICAL";
  m2.paddingLeft = 20;
  m2.paddingRight = 20;
  m2.paddingTop = 16;
  m2.itemSpacing = 12;

  const m2Head = figma.createFrame();
  m2Head.layoutMode = "HORIZONTAL";
  m2Head.primaryAxisAlignItems = "SPACE_BETWEEN";
  m2Head.counterAxisAlignItems = "CENTER";
  m2Head.resize(796, 30);
  m2Head.fills = [];
  m2Head.appendChild(createText("② Hồi quy tuyến tính & Gradient Descent", 18, FONT_SEMI, C.primary));
  m2Head.appendChild(makeBadge("Đang học (3/8)", C.accentTint, C.accentText));
  m2.appendChild(m2Head);

  const pillsRow = figma.createFrame();
  pillsRow.layoutMode = "HORIZONTAL";
  pillsRow.itemSpacing = 8;
  pillsRow.fills = [];
  pillsRow.appendChild(makeBadge("✓ Hàm mất mát", C.successTint, C.success));
  pillsRow.appendChild(makeBadge("✓ Đạo hàm riêng", C.successTint, C.success));
  pillsRow.appendChild(makeBadge("▶ Tốc độ học (α)", C.brandTint, C.primary));
  pillsRow.appendChild(makeBadge("Batch Gradient Descent", C.bgSubtle, C.textMuted));
  m2.appendChild(pillsRow);
  roadmapMain.appendChild(m2);

  bodyLayout.appendChild(roadmapMain);

  // Right Chat Col (380px)
  const chatCol = figma.createFrame();
  chatCol.resize(380, 736);
  chatCol.layoutMode = "VERTICAL";
  chatCol.fills = solidFill(C.surface);
  chatCol.strokes = [{ type: "SOLID", color: C.border }];
  chatCol.strokeWeight = 1;

  const chatHead = figma.createFrame();
  chatHead.resize(380, 56);
  chatHead.layoutMode = "HORIZONTAL";
  chatHead.primaryAxisAlignItems = "SPACE_BETWEEN";
  chatHead.counterAxisAlignItems = "CENTER";
  chatHead.paddingLeft = 20;
  chatHead.paddingRight = 20;
  chatHead.fills = solidFill(C.surface);
  chatHead.appendChild(createText("Trò chuyện (Lộ trình)", 16, FONT_SEMI, C.text));
  chatHead.appendChild(createText("+ Phiên mới", 13, FONT_SEMI, C.primary));
  chatCol.appendChild(chatHead);

  // Chat message
  const msgArea = figma.createFrame();
  msgArea.resize(380, 500);
  msgArea.layoutMode = "VERTICAL";
  msgArea.paddingLeft = 16;
  msgArea.paddingRight = 16;
  msgArea.paddingTop = 16;
  msgArea.itemSpacing = 16;
  msgArea.fills = solidFill(C.surface);

  const userBubble = figma.createFrame();
  userBubble.layoutMode = "VERTICAL";
  userBubble.paddingLeft = 14;
  userBubble.paddingRight = 14;
  userBubble.paddingTop = 10;
  userBubble.paddingBottom = 10;
  userBubble.cornerRadius = 14;
  userBubble.fills = solidFill(C.brandTint);
  userBubble.appendChild(createText("Học hết cuốn này cần đi qua những trụ cột nào?", 14, FONT_REG, C.text));
  msgArea.appendChild(userBubble);

  const aiText = createText("Lộ trình này gồm 3 trụ cột chính: Đại số tuyến tính, Mô hình có giám sát, và Đánh giá mô hình.", 14, FONT_REG, C.text);
  aiText.resize(348, 60);
  msgArea.appendChild(aiText);

  chatCol.appendChild(msgArea);
  bodyLayout.appendChild(chatCol);
  desktopRoadmap.appendChild(bodyLayout);

  figma.currentPage.appendChild(desktopRoadmap);
  createdNodes.push(desktopRoadmap);

  // ==========================================
  // 4. FRAME: AUTH & ERROR STATES (W-02 / W-24)
  // ==========================================
  const authFrame = figma.createFrame();
  authFrame.name = "4. Màn hình: Xác thực & Đăng nhập (W-02 Auth)";
  authFrame.x = 1320;
  authFrame.y = 540;
  authFrame.resize(1050, 736);
  authFrame.fills = solidFill(C.bgSubtle);
  authFrame.cornerRadius = 16;
  authFrame.strokes = [{ type: "SOLID", color: C.border }];
  authFrame.strokeWeight = 1;
  authFrame.layoutMode = "HORIZONTAL";
  authFrame.paddingTop = 24;
  authFrame.paddingBottom = 24;
  authFrame.paddingLeft = 24;
  authFrame.paddingRight = 24;
  authFrame.itemSpacing = 24;

  // Login Card
  const loginCard = figma.createFrame();
  loginCard.name = "Card Đăng nhập (/dang-nhap)";
  loginCard.resize(450, 680);
  loginCard.cornerRadius = 16;
  loginCard.fills = solidFill(C.surface);
  loginCard.strokes = [{ type: "SOLID", color: C.border }];
  loginCard.strokeWeight = 1;
  loginCard.layoutMode = "VERTICAL";
  loginCard.paddingLeft = 24;
  loginCard.paddingRight = 24;
  loginCard.paddingTop = 24;
  loginCard.itemSpacing = 14;

  loginCard.appendChild(createText("WayFinder", 22, FONT_BOLD, C.primary));
  loginCard.appendChild(createText("Đăng nhập tài khoản", 18, FONT_BOLD, C.text));
  loginCard.appendChild(createText("Học giáo trình cùng lộ trình thông minh", 13, FONT_REG, C.textMuted));

  // Error Alert Banner (invalid_credentials)
  const alertCard = figma.createFrame();
  alertCard.layoutMode = "HORIZONTAL";
  alertCard.counterAxisAlignItems = "CENTER";
  alertCard.resize(402, 44);
  alertCard.cornerRadius = 8;
  alertCard.fills = solidFill(C.dangerTint);
  alertCard.strokes = [{ type: "SOLID", color: C.danger }];
  alertCard.strokeWeight = 1;
  alertCard.paddingLeft = 12;
  alertCard.appendChild(createText("✕ Đăng nhập không thành công: Sai email hoặc mật khẩu", 12, FONT_SEMI, C.danger));
  loginCard.appendChild(alertCard);

  function makeInput(label, val) {
    const f = figma.createFrame();
    f.layoutMode = "VERTICAL";
    f.itemSpacing = 4;
    f.resize(402, 64);
    f.fills = [];
    f.appendChild(createText(label, 12, FONT_SEMI, C.text));
    const inp = figma.createFrame();
    inp.resize(402, 44);
    inp.cornerRadius = 8;
    inp.fills = solidFill(C.surface);
    inp.strokes = [{ type: "SOLID", color: C.borderInput }];
    inp.strokeWeight = 1;
    inp.paddingLeft = 14;
    inp.layoutMode = "HORIZONTAL";
    inp.counterAxisAlignItems = "CENTER";
    inp.appendChild(createText(val, 13, FONT_REG, C.text));
    f.appendChild(inp);
    return f;
  }

  loginCard.appendChild(makeInput("Email học viên", "hocvien@wayfinder.vn"));
  loginCard.appendChild(makeInput("Mật khẩu", "••••••••••••"));

  const loginBtn = makeButton("Đăng nhập (44px)", C.primary, C.white);
  loginBtn.resize(402, 44);
  loginCard.appendChild(loginBtn);
  authFrame.appendChild(loginCard);

  // Register Card & State Banners
  const regCard = figma.createFrame();
  regCard.name = "Card Đăng ký & Trạng thái lỗi W-02";
  regCard.resize(520, 680);
  regCard.cornerRadius = 16;
  regCard.fills = solidFill(C.surface);
  regCard.strokes = [{ type: "SOLID", color: C.border }];
  regCard.strokeWeight = 1;
  regCard.layoutMode = "VERTICAL";
  regCard.paddingLeft = 24;
  regCard.paddingRight = 24;
  regCard.paddingTop = 24;
  regCard.itemSpacing = 14;

  regCard.appendChild(createText("Trạng thái lỗi & Đăng ký W-02", 18, FONT_BOLD, C.text));

  // Rate limit banner
  const rateLimitCard = figma.createFrame();
  rateLimitCard.layoutMode = "HORIZONTAL";
  rateLimitCard.counterAxisAlignItems = "CENTER";
  rateLimitCard.resize(472, 44);
  rateLimitCard.cornerRadius = 8;
  rateLimitCard.fills = solidFill(C.accentTint);
  rateLimitCard.strokes = [{ type: "SOLID", color: C.accent }];
  rateLimitCard.strokeWeight = 1;
  rateLimitCard.paddingLeft = 12;
  rateLimitCard.appendChild(createText("⚠️ rate_limited: Bạn đã thử sai > 5 lần. Thử lại sau 15 phút.", 12, FONT_SEMI, C.accentText));
  regCard.appendChild(rateLimitCard);

  // Email unverified banner
  const verifyCard = figma.createFrame();
  verifyCard.layoutMode = "HORIZONTAL";
  verifyCard.counterAxisAlignItems = "CENTER";
  verifyCard.resize(472, 44);
  verifyCard.cornerRadius = 8;
  verifyCard.fills = solidFill(C.brandTint);
  verifyCard.strokes = [{ type: "SOLID", color: C.primary }];
  verifyCard.strokeWeight = 1;
  verifyCard.paddingLeft = 12;
  verifyCard.appendChild(createText("✉️ email_unverified: Cần xác minh email trước khi sử dụng.", 12, FONT_SEMI, C.primary));
  regCard.appendChild(verifyCard);

  regCard.appendChild(makeInput("Email đăng ký", "hocvien@truong.edu.vn"));
  regCard.appendChild(makeInput("Mật khẩu (Argon2id, 8-128 ký tự)", "••••••••••••"));
  regCard.appendChild(makeInput("Xác nhận mật khẩu", "••••••••••••"));

  const regBtn = makeButton("Đăng ký tài khoản (44px)", C.primary, C.white);
  regBtn.resize(472, 44);
  regCard.appendChild(regBtn);
  authFrame.appendChild(regCard);

  figma.currentPage.appendChild(authFrame);
  createdNodes.push(authFrame);

  // ==========================================
  // 5. FRAME: 4 PROTOTYPE FLOWS SPECIFICATION
  // ==========================================
  const protoFrame = figma.createFrame();
  protoFrame.name = "5. Đặc tả 4 Luồng Prototype (W-22 / W-24)";
  protoFrame.x = 0;
  protoFrame.y = 1380;
  protoFrame.resize(1280, 360);
  protoFrame.fills = solidFill(C.surface);
  protoFrame.cornerRadius = 16;
  protoFrame.strokes = [{ type: "SOLID", color: C.border }];
  protoFrame.strokeWeight = 1;
  protoFrame.layoutMode = "VERTICAL";
  protoFrame.paddingTop = 28;
  protoFrame.paddingBottom = 28;
  protoFrame.paddingLeft = 32;
  protoFrame.paddingRight = 32;
  protoFrame.itemSpacing = 16;

  protoFrame.appendChild(createText("4 Luồng Prototype Bấm được (Figma & Web Workbench)", 22, FONT_BOLD, C.text));
  protoFrame.appendChild(createText("Thời lượng tương tác: 120ms (nhanh), 200ms (chuẩn). Giảm chuyển động: ngắt hoạt ảnh, chuyển sang ảnh tĩnh.", 13, FONT_REG, C.textMuted));

  const protoGrid = figma.createFrame();
  protoGrid.layoutMode = "HORIZONTAL";
  protoGrid.itemSpacing = 16;
  protoGrid.fills = [];

  const flows = [
    { num: "Luồng 1", name: "Đăng nhập & Xác thực phiên", desc: "Màn hình /dang-nhap -> Form điền -> invalid_credentials -> Đăng nhập thành công -> /khoa-hoc", time: "120ms ease-out" },
    { num: "Luồng 2", name: "Tải sách & Dựng lộ trình", desc: "Trang /tai-len -> Kéo thả PDF -> Tiến trình 4 bước -> Spinner tĩnh khi reduce motion -> Lộ trình", time: "200ms ease" },
    { num: "Luồng 3", name: "Điều hướng & Học bài", desc: "Lộ trình /khoa-hoc/:cid -> Bấm Module 2 mở rộng -> Chọn khái niệm -> Mở lecture-2", time: "150ms ease-in-out" },
    { num: "Luồng 4", name: "Làm Quiz & Nhận phản hồi", desc: "Trang /quiz/:aid -> Bấm chọn đáp án B -> Nộp bài -> Tô màu success-tint kèm trích dẫn sách", time: "120ms ease" }
  ];

  for (const fl of flows) {
    const flCard = figma.createFrame();
    flCard.layoutMode = "VERTICAL";
    flCard.itemSpacing = 8;
    flCard.resize(290, 220);
    flCard.cornerRadius = 12;
    flCard.fills = solidFill(C.bgSubtle);
    flCard.strokes = [{ type: "SOLID", color: C.border }];
    flCard.strokeWeight = 1;
    flCard.paddingLeft = 16;
    flCard.paddingRight = 16;
    flCard.paddingTop = 16;
    flCard.paddingBottom = 16;

    flCard.appendChild(makeBadge(fl.num, C.brandTint, C.primary));
    flCard.appendChild(createText(fl.name, 15, FONT_SEMI, C.text));
    const descText = createText(fl.desc, 12, FONT_REG, C.textMuted);
    descText.resize(258, 70);
    flCard.appendChild(descText);
    flCard.appendChild(createText(`⏱ ${fl.time}`, 11, FONT_SEMI, C.primary));
    protoGrid.appendChild(flCard);
  }
  protoFrame.appendChild(protoGrid);

  figma.currentPage.appendChild(protoFrame);
  createdNodes.push(protoFrame);

  // Focus and Zoom
  figma.viewport.scrollAndZoomIntoView(createdNodes);
  figma.notify("🎉 WayFinder: Đã tự động vẽ toàn bộ Design System & Screens lên canvas!");
  figma.closePlugin();
})();
