/**
 * WayFinder Design Generator Figma Plugin (W-22)
 * Automatically draws the complete Design System, Components, and Screens
 * directly onto the Figma canvas using the native Figma Plugin API.
 */

(async () => {
  // 1. Color Palette Tokens & Hex-accurate parser from tokens.json
  function hexToRgb(hex) {
    hex = hex.replace('#', '').trim();
    if (hex.length === 3) {
      hex = hex.split('').map(c => c + c).join('');
    }
    const num = parseInt(hex, 16);
    return {
      r: Number((((num >> 16) & 255) / 255).toFixed(4)),
      g: Number((((num >> 8) & 255) / 255).toFixed(4)),
      b: Number(((num & 255) / 255).toFixed(4))
    };
  }

  const C = {
    bg: hexToRgb("#FFFFFF"),
    bgSubtle: hexToRgb("#F6F8FA"),
    surface: hexToRgb("#FFFFFF"),
    border: hexToRgb("#DDE2E8"),
    borderInput: hexToRgb("#8994A0"),
    text: hexToRgb("#12161B"),
    textMuted: hexToRgb("#5B6673"),
    brand: hexToRgb("#29A9FF"),
    brandTint: hexToRgb("#EAF6FF"),
    primary: hexToRgb("#0A6AB3"),
    primaryText: hexToRgb("#FFFFFF"),
    primaryHover: hexToRgb("#0A5E9C"),
    accent: hexToRgb("#FEBA4F"),
    accentTint: hexToRgb("#FFF4DF"),
    accentText: hexToRgb("#8A4F0F"),
    success: hexToRgb("#146C3B"),
    successTint: hexToRgb("#E8F6EE"),
    danger: hexToRgb("#B02F2F"),
    dangerTint: hexToRgb("#FDECEC"),
    white: { r: 1, g: 1, b: 1 },
  };

  const C_DARK = {
    bg: hexToRgb("#0E1217"),
    bgSubtle: hexToRgb("#161B22"),
    surface: hexToRgb("#161B22"),
    surface2: hexToRgb("#1E252E"),
    border: hexToRgb("#2A323C"),
    borderInput: hexToRgb("#6B7785"),
    text: hexToRgb("#E8EDF2"),
    textMuted: hexToRgb("#9AA6B2"),
    primary: hexToRgb("#29A9FF"),
    primaryText: hexToRgb("#0E1217"),
    primaryHover: hexToRgb("#52B8FF"),
    brand: hexToRgb("#29A9FF"),
    accent: hexToRgb("#FEBA4F"),
    accentText: hexToRgb("#FEBA4F"),
    success: hexToRgb("#4ADE80"),
    danger: hexToRgb("#F87171"),
    white: { r: 1, g: 1, b: 1 }
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

      let darkModeId = null;
      try {
        if (collection.modes.length > 1) {
          darkModeId = collection.modes[1].modeId;
        } else {
          darkModeId = collection.addMode("Dark");
        }
      } catch (modeErr) {
        console.log("Note: Single mode plan or addMode restriction:", modeErr);
      }

      let darkCollection = null;
      let darkColModeId = null;
      if (!darkModeId) {
        try {
          darkCollection = collections.find(c => c.name === "WayFinder Tokens (Dark)");
          if (!darkCollection) {
            darkCollection = figma.variables.createVariableCollection("WayFinder Tokens (Dark)");
          }
          darkColModeId = darkCollection.modes[0].modeId;
          darkCollection.renameMode(darkColModeId, "Dark");
        } catch (colErr) {
          console.log("Note: Dark collection fallback note:", colErr);
        }
      }

      const colorDefs = [
        { name: "color/primary", light: hexToRgb("#0A6AB3"), dark: hexToRgb("#29A9FF") },
        { name: "color/primary-text", light: hexToRgb("#FFFFFF"), dark: hexToRgb("#0E1217") },
        { name: "color/primary-hover", light: hexToRgb("#0A5E9C"), dark: hexToRgb("#52B8FF") },
        { name: "color/brand", light: hexToRgb("#29A9FF"), dark: hexToRgb("#29A9FF") },
        { name: "color/brand-tint", light: hexToRgb("#EAF6FF"), dark: hexToRgb("#29A9FF") },
        { name: "color/bg", light: hexToRgb("#FFFFFF"), dark: hexToRgb("#0E1217") },
        { name: "color/bg-subtle", light: hexToRgb("#F6F8FA"), dark: hexToRgb("#161B22") },
        { name: "color/surface", light: hexToRgb("#FFFFFF"), dark: hexToRgb("#161B22") },
        { name: "color/surface-2", light: hexToRgb("#FFFFFF"), dark: hexToRgb("#1E252E") },
        { name: "color/border", light: hexToRgb("#DDE2E8"), dark: hexToRgb("#2A323C") },
        { name: "color/border-input", light: hexToRgb("#8994A0"), dark: hexToRgb("#6B7785") },
        { name: "color/text", light: hexToRgb("#12161B"), dark: hexToRgb("#E8EDF2") },
        { name: "color/text-muted", light: hexToRgb("#5B6673"), dark: hexToRgb("#9AA6B2") },
        { name: "color/accent", light: hexToRgb("#FEBA4F"), dark: hexToRgb("#FEBA4F") },
        { name: "color/accent-tint", light: hexToRgb("#FFF4DF"), dark: hexToRgb("#FEBA4F") },
        { name: "color/accent-text", light: hexToRgb("#8A4F0F"), dark: hexToRgb("#FEBA4F") },
        { name: "color/success", light: hexToRgb("#146C3B"), dark: hexToRgb("#4ADE80") },
        { name: "color/success-tint", light: hexToRgb("#E8F6EE"), dark: hexToRgb("#4ADE80") },
        { name: "color/danger", light: hexToRgb("#B02F2F"), dark: hexToRgb("#F87171") },
        { name: "color/danger-tint", light: hexToRgb("#FDECEC"), dark: hexToRgb("#F87171") }
      ];

      for (const c of colorDefs) {
        try {
          const v = figma.variables.createVariable(c.name, collection, "COLOR");
          v.setValueForMode(lightModeId, c.light);
          if (darkModeId) {
            v.setValueForMode(darkModeId, c.dark);
          } else if (darkCollection && darkColModeId) {
            const vDark = figma.variables.createVariable(c.name, darkCollection, "COLOR");
            vDark.setValueForMode(darkColModeId, c.dark);
          }
        } catch (e) {}
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
        try {
          const v = figma.variables.createVariable(s.name, collection, "FLOAT");
          v.setValueForMode(lightModeId, s.val);
          if (darkModeId) {
            v.setValueForMode(darkModeId, s.val);
          } else if (darkCollection && darkColModeId) {
            const vDark = figma.variables.createVariable(s.name, darkCollection, "FLOAT");
            vDark.setValueForMode(darkColModeId, s.val);
          }
        } catch (e) {}
      }

      const radiusDefs = [
        { name: "radius/radius-sm", val: 6 },
        { name: "radius/radius-md", val: 10 },
        { name: "radius/radius-lg", val: 16 },
        { name: "radius/radius-full", val: 9999 }
      ];
      for (const r of radiusDefs) {
        try {
          const v = figma.variables.createVariable(r.name, collection, "FLOAT");
          v.setValueForMode(lightModeId, r.val);
          if (darkModeId) {
            v.setValueForMode(darkModeId, r.val);
          } else if (darkCollection && darkColModeId) {
            const vDark = figma.variables.createVariable(r.name, darkCollection, "FLOAT");
            vDark.setValueForMode(darkColModeId, r.val);
          }
        } catch (e) {}
      }

      const motionDefs = [
        { name: "motion/motion-fast", val: 120 },
        { name: "motion/motion-normal", val: 200 },
        { name: "motion/motion-slow", val: 300 }
      ];
      for (const m of motionDefs) {
        try {
          const v = figma.variables.createVariable(m.name, collection, "FLOAT");
          v.setValueForMode(lightModeId, m.val);
          if (darkModeId) {
            v.setValueForMode(darkModeId, m.val);
          } else if (darkCollection && darkColModeId) {
            const vDark = figma.variables.createVariable(m.name, darkCollection, "FLOAT");
            vDark.setValueForMode(darkColModeId, m.val);
          }
        } catch (e) {}
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
  tokensFrame.resize(900, 560);
  tokensFrame.fills = solidFill(C.surface);
  tokensFrame.cornerRadius = 16;
  tokensFrame.strokes = [{ type: "SOLID", color: C.border }];
  tokensFrame.strokeWeight = 1;
  tokensFrame.layoutMode = "VERTICAL";
  tokensFrame.paddingTop = 28;
  tokensFrame.paddingBottom = 28;
  tokensFrame.paddingLeft = 32;
  tokensFrame.paddingRight = 32;
  tokensFrame.itemSpacing = 14;

  const tokenTitle = createText("WayFinder — Hệ màu & Tokens (W-22 / W-24)", 22, FONT_BOLD, C.text);
  tokensFrame.appendChild(tokenTitle);

  tokensFrame.appendChild(createText("Bảng màu Chế độ Sáng (Light Mode)", 14, FONT_SEMI, C.primary));
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
    box.itemSpacing = 4;
    box.resize(120, 115);
    box.cornerRadius = 10;
    box.fills = solidFill(C.bgSubtle);
    box.paddingTop = 10;
    box.paddingBottom = 10;
    box.paddingLeft = 10;
    box.paddingRight = 10;

    const colorCircle = figma.createFrame();
    colorCircle.resize(36, 36);
    colorCircle.cornerRadius = 18;
    colorCircle.fills = solidFill(item.c);
    box.appendChild(colorCircle);

    box.appendChild(createText(item.name, 12, FONT_SEMI, C.text));
    box.appendChild(createText(item.hex, 11, FONT_REG, C.textMuted));
    box.appendChild(createText(item.note, 10, FONT_REG, C.textMuted));

    swatchesRow.appendChild(box);
  }
  tokensFrame.appendChild(swatchesRow);

  // Dark Swatches Row
  tokensFrame.appendChild(createText("Bảng màu Chế độ Tối (Dark Mode — Chuẩn 100% tokens.json)", 14, FONT_SEMI, C.primary));
  const darkSwatchesRow = figma.createFrame();
  darkSwatchesRow.layoutMode = "HORIZONTAL";
  darkSwatchesRow.itemSpacing = 16;
  darkSwatchesRow.fills = [];

  const darkTokenList = [
    { name: "Primary Dark", hex: "#29A9FF", c: C_DARK.primary, note: "Nút tối (7.35:1)" },
    { name: "Background", hex: "#0E1217", c: C_DARK.bg, note: "Nền chính tối" },
    { name: "Surface", hex: "#161B22", c: C_DARK.surface, note: "Thẻ panel tối" },
    { name: "Text Main", hex: "#E8EDF2", c: C_DARK.text, note: "Chữ chính (15.8:1)" },
    { name: "Success", hex: "#4ADE80", c: C_DARK.success, note: "Đã học (9.2:1)" },
    { name: "Danger", hex: "#F87171", c: C_DARK.danger, note: "Lỗi tối (6.5:1)" }
  ];

  for (const item of darkTokenList) {
    const box = figma.createFrame();
    box.layoutMode = "VERTICAL";
    box.itemSpacing = 4;
    box.resize(120, 115);
    box.cornerRadius = 10;
    box.fills = solidFill(C.bgSubtle);
    box.paddingTop = 10;
    box.paddingBottom = 10;
    box.paddingLeft = 10;
    box.paddingRight = 10;

    const colorCircle = figma.createFrame();
    colorCircle.resize(36, 36);
    colorCircle.cornerRadius = 18;
    colorCircle.fills = solidFill(item.c);
    box.appendChild(colorCircle);

    box.appendChild(createText(item.name, 12, FONT_SEMI, C.text));
    box.appendChild(createText(item.hex, 11, FONT_REG, C.textMuted));
    box.appendChild(createText(item.note, 10, FONT_REG, C.textMuted));

    darkSwatchesRow.appendChild(box);
  }
  tokensFrame.appendChild(darkSwatchesRow);

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

  // Native Figma Components
  if (typeof figma.createComponent === "function") {
    try {
      const compBtnPrimary = figma.createComponent();
      compBtnPrimary.name = "Component / Button Primary";
      compBtnPrimary.layoutMode = "HORIZONTAL";
      compBtnPrimary.primaryAxisAlignItems = "CENTER";
      compBtnPrimary.counterAxisAlignItems = "CENTER";
      compBtnPrimary.paddingLeft = 16; compBtnPrimary.paddingRight = 16;
      compBtnPrimary.paddingTop = 10; compBtnPrimary.paddingBottom = 10;
      compBtnPrimary.cornerRadius = 10;
      compBtnPrimary.fills = solidFill(C.primary);
      compBtnPrimary.appendChild(createText("Nút chính (Primary)", 14, FONT_SEMI, C.white));
      compFrame.appendChild(compBtnPrimary);

      const compBadgeSuccess = figma.createComponent();
      compBadgeSuccess.name = "Component / Badge Success";
      compBadgeSuccess.layoutMode = "HORIZONTAL";
      compBadgeSuccess.paddingLeft = 8; compBadgeSuccess.paddingRight = 8;
      compBadgeSuccess.paddingTop = 4; compBadgeSuccess.paddingBottom = 4;
      compBadgeSuccess.cornerRadius = 6;
      compBadgeSuccess.fills = solidFill(C.successTint);
      compBadgeSuccess.appendChild(createText("✓ Hoàn thành", 12, FONT_SEMI, C.success));
      compFrame.appendChild(compBadgeSuccess);
    } catch (compErr) {
      console.log("Component creation notice:", compErr);
    }
  }

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

  // Reaction status tracking
  const reactionStats = {
    attempted: 0,
    linked: 0,
    failed: 0,
    details: []
  };

  // Helper to link Figma Prototype Reactions (ON_CLICK -> NAVIGATE)
  async function linkReaction(sourceNode, targetFrame, description = "") {
    if (!sourceNode || !targetFrame) return false;
    reactionStats.attempted++;
    const desc = description || (sourceNode.name || "Source") + " -> " + (targetFrame.name || "Target");
    try {
      if (typeof sourceNode.setReactionsAsync === "function") {
        await sourceNode.setReactionsAsync([
          {
            trigger: { type: "ON_CLICK" },
            actions: [
              {
                type: "NODE",
                destinationId: targetFrame.id,
                navigation: "NAVIGATE",
                transition: {
                  type: "DISSOLVE",
                  easing: { type: "EASE_OUT" },
                  duration: 0.15
                }
              }
            ]
          }
        ]);
        reactionStats.linked++;
        reactionStats.details.push({ flow: desc, status: "LINKED_ASYNC" });
        return true;
      } else if ("reactions" in sourceNode) {
        sourceNode.reactions = [
          {
            trigger: { type: "ON_CLICK" },
            action: {
              type: "NODE",
              destinationId: targetFrame.id,
              navigation: "NAVIGATE"
            }
          }
        ];
        reactionStats.linked++;
        reactionStats.details.push({ flow: desc, status: "LINKED_SYNC" });
        return true;
      } else {
        reactionStats.failed++;
        reactionStats.details.push({ flow: desc, status: "MANUAL_REQUIRED", reason: "API reaction không khả dụng trên node hoặc phiên bản Figma" });
        return false;
      }
    } catch (reactionErr) {
      reactionStats.failed++;
      reactionStats.details.push({ flow: desc, status: "FAILED", error: String(reactionErr) });
      console.log("Reaction setup note:", reactionErr);
      return false;
    }
  }

  // ==========================================
  // 5. FRAME: MÀN HÌNH W-03 (XÁC THỰC EMAIL & ĐẶT LẠI MẬT KHẨU)
  // ==========================================
  const w03Frame = figma.createFrame();
  w03Frame.name = "5. Màn hình W-03: Xác thực Email & Đặt lại Mật khẩu";
  w03Frame.x = 0;
  w03Frame.y = 1380;
  w03Frame.resize(1280, 520);
  w03Frame.fills = solidFill(C.surface);
  w03Frame.cornerRadius = 16;
  w03Frame.strokes = [{ type: "SOLID", color: C.border }];
  w03Frame.strokeWeight = 1;
  w03Frame.layoutMode = "VERTICAL";
  w03Frame.paddingTop = 28;
  w03Frame.paddingBottom = 28;
  w03Frame.paddingLeft = 32;
  w03Frame.paddingRight = 32;
  w03Frame.itemSpacing = 16;

  w03Frame.appendChild(createText("Bộ màn hình W-03: Xác thực Email, Quên & Đặt lại mật khẩu (Token một lần)", 22, FONT_BOLD, C.text));
  w03Frame.appendChild(createText("Bàn giao chuẩn phục vụ nhóm Web (W-03) • Viewport thích ứng • Nút 44px • WCAG 2.1 AA", 13, FONT_REG, C.textMuted));

  const w03CardsRow = figma.createFrame();
  w03CardsRow.layoutMode = "HORIZONTAL";
  w03CardsRow.itemSpacing = 16;
  w03CardsRow.fills = [];

  // Card 1: Chờ xác minh email
  const cardVerify = figma.createFrame();
  cardVerify.layoutMode = "VERTICAL";
  cardVerify.itemSpacing = 10;
  cardVerify.resize(288, 380);
  cardVerify.cornerRadius = 12;
  cardVerify.fills = solidFill(C.bgSubtle);
  cardVerify.strokes = [{ type: "SOLID", color: C.border }];
  cardVerify.strokeWeight = 1;
  cardVerify.paddingLeft = 16;
  cardVerify.paddingRight = 16;
  cardVerify.paddingTop = 16;
  cardVerify.paddingBottom = 16;
  cardVerify.appendChild(makeBadge("W-03: Màn 1", C.brandTint, C.primary));
  cardVerify.appendChild(createText("Chờ xác minh email", 16, FONT_SEMI, C.text));
  const bannerV = figma.createFrame();
  bannerV.resize(256, 60);
  bannerV.cornerRadius = 8;
  bannerV.fills = solidFill(C.brandTint);
  bannerV.paddingLeft = 10;
  bannerV.paddingRight = 10;
  bannerV.paddingTop = 8;
  bannerV.appendChild(createText("✉️ Đã gửi email xác minh đến bacsi.nguyen@benhvien.vn. Vui lòng kiểm tra hộp thư.", 11, FONT_REG, C.primary));
  cardVerify.appendChild(bannerV);
  const btnResend = makeButton("Gửi lại email (60s)", C.bgSubtle, C.text);
  btnResend.resize(256, 44);
  btnResend.strokes = [{ type: "SOLID", color: C.border }];
  cardVerify.appendChild(btnResend);
  const btnCont = makeButton("Đã xác minh, tiếp tục", C.primary, C.white);
  btnCont.resize(256, 44);
  cardVerify.appendChild(btnCont);
  w03CardsRow.appendChild(cardVerify);

  // Card 2: Quên mật khẩu
  const cardForgot = figma.createFrame();
  cardForgot.layoutMode = "VERTICAL";
  cardForgot.itemSpacing = 10;
  cardForgot.resize(288, 380);
  cardForgot.cornerRadius = 12;
  cardForgot.fills = solidFill(C.bgSubtle);
  cardForgot.strokes = [{ type: "SOLID", color: C.border }];
  cardForgot.strokeWeight = 1;
  cardForgot.paddingLeft = 16;
  cardForgot.paddingRight = 16;
  cardForgot.paddingTop = 16;
  cardForgot.paddingBottom = 16;
  cardForgot.appendChild(makeBadge("W-03: Màn 2", C.brandTint, C.primary));
  cardForgot.appendChild(createText("Quên mật khẩu", 16, FONT_SEMI, C.text));
  cardForgot.appendChild(createText("Nhập email để nhận liên kết đặt lại mật khẩu có hiệu lực 60 phút:", 12, FONT_REG, C.textMuted));
  cardForgot.appendChild(makeInput("Email tài khoản", "bacsi.nguyen@benhvien.vn"));
  const btnSendReset = makeButton("Gửi liên kết đặt lại (44px)", C.primary, C.white);
  btnSendReset.resize(256, 44);
  cardForgot.appendChild(btnSendReset);
  w03CardsRow.appendChild(cardForgot);

  // Card 3: Đặt lại mật khẩu mới
  const cardReset = figma.createFrame();
  cardReset.layoutMode = "VERTICAL";
  cardReset.itemSpacing = 10;
  cardReset.resize(288, 380);
  cardReset.cornerRadius = 12;
  cardReset.fills = solidFill(C.bgSubtle);
  cardReset.strokes = [{ type: "SOLID", color: C.border }];
  cardReset.strokeWeight = 1;
  cardReset.paddingLeft = 16;
  cardReset.paddingRight = 16;
  cardReset.paddingTop = 16;
  cardReset.paddingBottom = 16;
  cardReset.appendChild(makeBadge("W-03: Màn 3", C.brandTint, C.primary));
  cardReset.appendChild(createText("Đặt lại mật khẩu mới", 16, FONT_SEMI, C.text));
  cardReset.appendChild(makeInput("Mật khẩu mới", "••••••••••••"));
  cardReset.appendChild(makeInput("Xác nhận mật khẩu", "••••••••••••"));
  const btnUpdatePass = makeButton("Lưu mật khẩu & Đăng nhập", C.primary, C.white);
  btnUpdatePass.resize(256, 44);
  cardReset.appendChild(btnUpdatePass);
  w03CardsRow.appendChild(cardReset);

  // Card 4: Token hết hạn / đã dùng
  const cardExpired = figma.createFrame();
  cardExpired.layoutMode = "VERTICAL";
  cardExpired.itemSpacing = 10;
  cardExpired.resize(288, 380);
  cardExpired.cornerRadius = 12;
  cardExpired.fills = solidFill(C.bgSubtle);
  cardExpired.strokes = [{ type: "SOLID", color: C.border }];
  cardExpired.strokeWeight = 1;
  cardExpired.paddingLeft = 16;
  cardExpired.paddingRight = 16;
  cardExpired.paddingTop = 16;
  cardExpired.paddingBottom = 16;
  cardExpired.appendChild(makeBadge("W-03: Màn 4", C.dangerTint, C.danger));
  cardExpired.appendChild(createText("Token không hợp lệ", 16, FONT_SEMI, C.danger));
  const bannerExp = figma.createFrame();
  bannerExp.resize(256, 80);
  bannerExp.cornerRadius = 8;
  bannerExp.fills = solidFill(C.dangerTint);
  bannerExp.paddingLeft = 10;
  bannerExp.paddingRight = 10;
  bannerExp.paddingTop = 8;
  bannerExp.appendChild(createText("⚠️ Liên kết đã hết hạn hoặc đã được sử dụng. Xác minh email có hiệu lực 24 giờ; đặt lại mật khẩu có hiệu lực 60 phút.", 11, FONT_REG, C.danger));
  cardExpired.appendChild(bannerExp);
  const btnReqNew = makeButton("Yêu cầu gửi liên kết mới", C.primary, C.white);
  btnReqNew.resize(256, 44);
  cardExpired.appendChild(btnReqNew);
  w03CardsRow.appendChild(cardExpired);

  w03Frame.appendChild(w03CardsRow);
  figma.currentPage.appendChild(w03Frame);
  createdNodes.push(w03Frame);

  // ==========================================
  // 6. FRAME: 4 BỘ PROTOTYPE LIÊN KẾT BẤM ĐƯỢC (FIGMA PROTOTYPE REACTIONS)
  // ==========================================
  const protoMasterFrame = figma.createFrame();
  protoMasterFrame.name = "6. 4 Luồng Prototype Bấm được (Figma Reactions Linked)";
  protoMasterFrame.x = 0;
  protoMasterFrame.y = 1960;
  protoMasterFrame.resize(1280, 860);
  protoMasterFrame.fills = solidFill(C.surface);
  protoMasterFrame.cornerRadius = 16;
  protoMasterFrame.strokes = [{ type: "SOLID", color: C.border }];
  protoMasterFrame.strokeWeight = 1;
  protoMasterFrame.layoutMode = "VERTICAL";
  protoMasterFrame.paddingTop = 28;
  protoMasterFrame.paddingBottom = 28;
  protoMasterFrame.paddingLeft = 32;
  protoMasterFrame.paddingRight = 32;
  protoMasterFrame.itemSpacing = 20;

  protoMasterFrame.appendChild(createText("4 Luồng Prototype Bấm được (Figma Reactions & Web Workbench)", 22, FONT_BOLD, C.text));
  protoMasterFrame.appendChild(createText("Kiểm tra báo cáo reactions sau khi chạy plugin; nối thủ công các mục chưa thành công trước khi bấm Present.", 13, FONT_REG, C.textMuted));

  const protoRows = figma.createFrame();
  protoRows.layoutMode = "VERTICAL";
  protoRows.itemSpacing = 16;
  protoRows.fills = [];

  // --- LUỒNG 1: ONBOARDING (Register -> Courses -> Lecture) ---
  const flow1Container = figma.createFrame();
  flow1Container.name = "Luồng 1: Đăng ký -> Khoá học -> Bài giảng";
  flow1Container.layoutMode = "HORIZONTAL";
  flow1Container.itemSpacing = 14;
  flow1Container.fills = [];

  // Frame 1A: Register
  const f1A = figma.createFrame();
  f1A.name = "F1A: Đăng ký học viên";
  f1A.resize(288, 160);
  f1A.cornerRadius = 10;
  f1A.fills = solidFill(C.bgSubtle);
  f1A.strokes = [{ type: "SOLID", color: C.border }];
  f1A.paddingLeft = 14; f1A.paddingRight = 14; f1A.paddingTop = 14; f1A.paddingBottom = 14;
  f1A.layoutMode = "VERTICAL"; f1A.itemSpacing = 8;
  f1A.appendChild(makeBadge("Luồng 1 • Bước 1", C.brandTint, C.primary));
  f1A.appendChild(createText("Đăng ký tài khoản", 14, FONT_SEMI, C.text));
  const f1ABtn = makeButton("Đăng ký & Vào khoá học ➔", C.primary, C.white);
  f1ABtn.resize(260, 44);
  f1A.appendChild(f1ABtn);
  flow1Container.appendChild(f1A);

  // Frame 1B: Courses
  const f1B = figma.createFrame();
  f1B.name = "F1B: Khoá học của tôi";
  f1B.resize(288, 160);
  f1B.cornerRadius = 10;
  f1B.fills = solidFill(C.bgSubtle);
  f1B.strokes = [{ type: "SOLID", color: C.border }];
  f1B.paddingLeft = 14; f1B.paddingRight = 14; f1B.paddingTop = 14; f1B.paddingBottom = 14;
  f1B.layoutMode = "VERTICAL"; f1B.itemSpacing = 8;
  f1B.appendChild(makeBadge("Luồng 1 • Bước 2", C.successTint, C.success));
  f1B.appendChild(createText("Khoá học: Bác sĩ Nội trú", 14, FONT_SEMI, C.text));
  const f1BBtn = makeButton("Mở bài lecture-2 ➔", C.primary, C.white);
  f1BBtn.resize(260, 44);
  f1B.appendChild(f1BBtn);
  flow1Container.appendChild(f1B);

  // Frame 1C: Lecture
  const f1C = figma.createFrame();
  f1C.name = "F1C: Bài giảng lecture-2";
  f1C.resize(288, 160);
  f1C.cornerRadius = 10;
  f1C.fills = solidFill(C.bgSubtle);
  f1C.strokes = [{ type: "SOLID", color: C.primary }];
  f1C.strokeWeight = 2;
  f1C.paddingLeft = 14; f1C.paddingRight = 14; f1C.paddingTop = 14; f1C.paddingBottom = 14;
  f1C.layoutMode = "VERTICAL"; f1C.itemSpacing = 8;
  f1C.appendChild(makeBadge("Luồng 1 • Bước 3", C.brandTint, C.primary));
  f1C.appendChild(createText("lecture-2: Giải phẫu động mạch", 14, FONT_SEMI, C.text));
  f1C.appendChild(createText("✓ Accordion mở • Nội dung sẵn sàng", 12, FONT_REG, C.success));
  flow1Container.appendChild(f1C);

  // Connect Flow 1 prototype reactions
  await linkReaction(f1ABtn, f1B);
  await linkReaction(f1BBtn, f1C);
  protoRows.appendChild(flow1Container);

  // --- LUỒNG 2: CHIA SẺ & THAM GIA ---
  const flow2Container = figma.createFrame();
  flow2Container.name = "Luồng 2: Chia sẻ -> Tham gia khoá học";
  flow2Container.layoutMode = "HORIZONTAL";
  flow2Container.itemSpacing = 14;
  flow2Container.fills = [];

  const f2A = figma.createFrame();
  f2A.name = "F2A: Khoá học & Mã chia sẻ";
  f2A.resize(288, 160); f2A.cornerRadius = 10; f2A.fills = solidFill(C.bgSubtle);
  f2A.strokes = [{ type: "SOLID", color: C.border }];
  f2A.paddingLeft = 14; f2A.paddingRight = 14; f2A.paddingTop = 14; f2A.paddingBottom = 14;
  f2A.layoutMode = "VERTICAL"; f2A.itemSpacing = 8;
  f2A.appendChild(makeBadge("Luồng 2 • Bước 1", C.brandTint, C.primary));
  f2A.appendChild(createText("Chia sẻ: WF-PHARM-2026", 14, FONT_SEMI, C.text));
  const f2ABtn = makeButton("Mở liên kết tham gia ➔", C.primary, C.white);
  f2ABtn.resize(260, 44);
  f2A.appendChild(f2ABtn);
  flow2Container.appendChild(f2A);

  const f2B = figma.createFrame();
  f2B.name = "F2B: Xác nhận tham gia";
  f2B.resize(288, 160); f2B.cornerRadius = 10; f2B.fills = solidFill(C.bgSubtle);
  f2B.strokes = [{ type: "SOLID", color: C.border }];
  f2B.paddingLeft = 14; f2B.paddingRight = 14; f2B.paddingTop = 14; f2B.paddingBottom = 14;
  f2B.layoutMode = "VERTICAL"; f2B.itemSpacing = 8;
  f2B.appendChild(makeBadge("Luồng 2 • Bước 2", C.accentTint, C.accentText));
  f2B.appendChild(createText("Xác nhận vào Dược lý", 14, FONT_SEMI, C.text));
  const f2BBtn = makeButton("Xác nhận tham gia ➔", C.primary, C.white);
  f2BBtn.resize(260, 44);
  f2B.appendChild(f2BBtn);
  flow2Container.appendChild(f2B);

  const f2C = figma.createFrame();
  f2C.name = "F2C: Tham gia thành công";
  f2C.resize(288, 160); f2C.cornerRadius = 10; f2C.fills = solidFill(C.bgSubtle);
  f2C.strokes = [{ type: "SOLID", color: C.success }]; f2C.strokeWeight = 2;
  f2C.paddingLeft = 14; f2C.paddingRight = 14; f2C.paddingTop = 14; f2C.paddingBottom = 14;
  f2C.layoutMode = "VERTICAL"; f2C.itemSpacing = 8;
  f2C.appendChild(makeBadge("Luồng 2 • Bước 3", C.successTint, C.success));
  f2C.appendChild(createText("Đã là thành viên chính thức", 14, FONT_SEMI, C.text));
  f2C.appendChild(createText("✓ Quyền truy cập đã kích hoạt", 12, FONT_REG, C.success));
  flow2Container.appendChild(f2C);

  await linkReaction(f2ABtn, f2B);
  await linkReaction(f2BBtn, f2C);
  protoRows.appendChild(flow2Container);

  // --- LUỒNG 3: TẢI SÁCH -> DỰNG LỘ TRÌNH ---
  const flow3Container = figma.createFrame();
  flow3Container.name = "Luồng 3: Tải sách -> Dựng lộ trình";
  flow3Container.layoutMode = "HORIZONTAL";
  flow3Container.itemSpacing = 14;
  flow3Container.fills = [];

  const f3A = figma.createFrame();
  f3A.name = "F3A: Tải sách PDF";
  f3A.resize(288, 160); f3A.cornerRadius = 10; f3A.fills = solidFill(C.bgSubtle);
  f3A.strokes = [{ type: "SOLID", color: C.border }];
  f3A.paddingLeft = 14; f3A.paddingRight = 14; f3A.paddingTop = 14; f3A.paddingBottom = 14;
  f3A.layoutMode = "VERTICAL"; f3A.itemSpacing = 8;
  f3A.appendChild(makeBadge("Luồng 3 • Bước 1", C.brandTint, C.primary));
  f3A.appendChild(createText("Kéo thả Harrison.pdf", 14, FONT_SEMI, C.text));
  const f3ABtn = makeButton("Chọn tệp & Cấu hình ➔", C.primary, C.white);
  f3ABtn.resize(260, 44);
  f3A.appendChild(f3ABtn);
  flow3Container.appendChild(f3A);

  const f3B = figma.createFrame();
  f3B.name = "F3B: Cấu hình mục tiêu";
  f3B.resize(288, 160); f3B.cornerRadius = 10; f3B.fills = solidFill(C.bgSubtle);
  f3B.strokes = [{ type: "SOLID", color: C.border }];
  f3B.paddingLeft = 14; f3B.paddingRight = 14; f3B.paddingTop = 14; f3B.paddingBottom = 14;
  f3B.layoutMode = "VERTICAL"; f3B.itemSpacing = 8;
  f3B.appendChild(makeBadge("Luồng 3 • Bước 2", C.accentTint, C.accentText));
  f3B.appendChild(createText("Mục tiêu: Bác sĩ Nội trú", 14, FONT_SEMI, C.text));
  const f3BBtn = makeButton("Bắt đầu dựng lộ trình ➔", C.primary, C.white);
  f3BBtn.resize(260, 44);
  f3B.appendChild(f3BBtn);
  flow3Container.appendChild(f3B);

  const f3C = figma.createFrame();
  f3C.name = "F3C: Lộ trình hoàn tất";
  f3C.resize(288, 160); f3C.cornerRadius = 10; f3C.fills = solidFill(C.bgSubtle);
  f3C.strokes = [{ type: "SOLID", color: C.success }]; f3C.strokeWeight = 2;
  f3C.paddingLeft = 14; f3C.paddingRight = 14; f3C.paddingTop = 14; f3C.paddingBottom = 14;
  f3C.layoutMode = "VERTICAL"; f3C.itemSpacing = 8;
  f3C.appendChild(makeBadge("Luồng 3 • Bước 3", C.successTint, C.success));
  f3C.appendChild(createText("Lộ trình 18 khái niệm", 14, FONT_SEMI, C.text));
  f3C.appendChild(createText("✓ Tiến trình 4 bước đã hoàn tất", 12, FONT_REG, C.success));
  flow3Container.appendChild(f3C);

  await linkReaction(f3ABtn, f3B);
  await linkReaction(f3BBtn, f3C);
  protoRows.appendChild(flow3Container);

  // --- LUỒNG 4: QUIZ -> NỘP BÀI -> KẾT QUẢ ---
  const flow4Container = figma.createFrame();
  flow4Container.name = "Luồng 4: Quiz -> Nộp bài -> Kết quả & Trích dẫn";
  flow4Container.layoutMode = "HORIZONTAL";
  flow4Container.itemSpacing = 14;
  flow4Container.fills = [];

  const f4A = figma.createFrame();
  f4A.name = "F4A: Làm câu hỏi Quiz";
  f4A.resize(288, 160); f4A.cornerRadius = 10; f4A.fills = solidFill(C.bgSubtle);
  f4A.strokes = [{ type: "SOLID", color: C.border }];
  f4A.paddingLeft = 14; f4A.paddingRight = 14; f4A.paddingTop = 14; f4A.paddingBottom = 14;
  f4A.layoutMode = "VERTICAL"; f4A.itemSpacing = 8;
  f4A.appendChild(makeBadge("Luồng 4 • Bước 1", C.brandTint, C.primary));
  f4A.appendChild(createText("Chọn đáp án B: Nhánh LAD", 14, FONT_SEMI, C.text));
  const f4ABtn = makeButton("Nộp bài & Chấm điểm ➔", C.primary, C.white);
  f4ABtn.resize(260, 44);
  f4A.appendChild(f4ABtn);
  flow4Container.appendChild(f4A);

  const f4B = figma.createFrame();
  f4B.name = "F4B: Kết quả & Trích dẫn sách";
  f4B.resize(288, 160); f4B.cornerRadius = 10; f4B.fills = solidFill(C.bgSubtle);
  f4B.strokes = [{ type: "SOLID", color: C.success }]; f4B.strokeWeight = 2;
  f4B.paddingLeft = 14; f4B.paddingRight = 14; f4B.paddingTop = 14; f4B.paddingBottom = 14;
  f4B.layoutMode = "VERTICAL"; f4B.itemSpacing = 8;
  f4B.appendChild(makeBadge("Luồng 4 • Bước 2", C.successTint, C.success));
  f4B.appendChild(createText("Chính xác: 10/10 điểm", 14, FONT_SEMI, C.success));
  f4B.appendChild(createText("📖 Trích dẫn: Harrison 21st, Tr. 1892", 11, FONT_REG, C.textMuted));
  flow4Container.appendChild(f4B);

  await linkReaction(f4ABtn, f4B);
  protoRows.appendChild(flow4Container);

  protoMasterFrame.appendChild(protoRows);
  figma.currentPage.appendChild(protoMasterFrame);
  createdNodes.push(protoMasterFrame);

  // Native Figma Flow Starting Points (4 Core Flows)
  try {
    figma.currentPage.flowStartingPoints = [
      { nodeId: f1A.id, name: "Luồng 1: Đăng ký -> Khoá học -> Bài giảng" },
      { nodeId: f2A.id, name: "Luồng 2: Chia sẻ -> Tham gia khoá học" },
      { nodeId: f3A.id, name: "Luồng 3: Tải giáo trình -> Dựng 4 bước" },
      { nodeId: f4A.id, name: "Luồng 4: Quiz -> Chấm điểm -> Trích dẫn" }
    ];
  } catch (flowErr) {
    console.log("Flow starting points notice:", flowErr);
  }

  // ==========================================
  // 7. FRAME: MÀN HÌNH W-06 (KHOÁ HỌC CỦA TÔI /khoa-hoc)
  // ==========================================
  const w06Frame = figma.createFrame();
  w06Frame.name = "7. Màn hình W-06: Khoá học của tôi (/khoa-hoc)";
  w06Frame.x = 0;
  w06Frame.y = 2880;
  w06Frame.resize(1280, 600);
  w06Frame.fills = solidFill(C.surface);
  w06Frame.cornerRadius = 16;
  w06Frame.strokes = [{ type: "SOLID", color: C.border }];
  w06Frame.strokeWeight = 1;
  w06Frame.layoutMode = "VERTICAL";
  w06Frame.paddingTop = 28;
  w06Frame.paddingBottom = 28;
  w06Frame.paddingLeft = 32;
  w06Frame.paddingRight = 32;
  w06Frame.itemSpacing = 20;

  w06Frame.appendChild(createText("Khoá học của tôi (/khoa-hoc) — 4 Trạng thái (W-06)", 22, FONT_BOLD, C.text));
  w06Frame.appendChild(createText("Bao gồm: Thẻ khoá học đang học (DOC-SAMPLE-01), Trạng thái rỗng, Shimmer Skeleton khi tải, và Banner cảnh báo lỗi.", 13, FONT_REG, C.textMuted));

  const w06CardsRow = figma.createFrame();
  w06CardsRow.layoutMode = "HORIZONTAL";
  w06CardsRow.itemSpacing = 16;
  w06CardsRow.fills = [];

  // State 1: Active Course Card (DOC-SAMPLE-01)
  const cardActive = figma.createFrame();
  cardActive.layoutMode = "VERTICAL";
  cardActive.itemSpacing = 12;
  cardActive.resize(288, 440);
  cardActive.cornerRadius = 12;
  cardActive.fills = solidFill(C.bgSubtle);
  cardActive.strokes = [{ type: "SOLID", color: C.primary }];
  cardActive.strokeWeight = 2;
  cardActive.paddingLeft = 16;
  cardActive.paddingRight = 16;
  cardActive.paddingTop = 16;
  cardActive.paddingBottom = 16;
  cardActive.appendChild(makeBadge("W-06: Đang học", C.brandTint, C.primary));
  cardActive.appendChild(createText("Giải phẫu Tim mạch", 16, FONT_SEMI, C.text));
  cardActive.appendChild(createText("Mã: DOC-SAMPLE-01", 12, FONT_REG, C.textMuted));
  cardActive.appendChild(createText("Tiến độ: 12/18 khái niệm (67%)", 13, FONT_SEMI, C.primary));

  const progBar = figma.createFrame();
  progBar.resize(256, 8);
  progBar.cornerRadius = 4;
  progBar.fills = solidFill(C.border);
  const progFill = figma.createFrame();
  progFill.resize(170, 8);
  progFill.cornerRadius = 4;
  progFill.fills = solidFill(C.brand);
  progBar.appendChild(progFill);
  cardActive.appendChild(progBar);

  const btnContStudy = makeButton("Tiếp tục học ➔", C.primary, C.white);
  btnContStudy.resize(256, 44);
  cardActive.appendChild(btnContStudy);
  w06CardsRow.appendChild(cardActive);

  // State 2: Empty State
  const cardEmpty = figma.createFrame();
  cardEmpty.layoutMode = "VERTICAL";
  cardEmpty.itemSpacing = 12;
  cardEmpty.resize(288, 440);
  cardEmpty.cornerRadius = 12;
  cardEmpty.fills = solidFill(C.bgSubtle);
  cardEmpty.strokes = [{ type: "SOLID", color: C.border }];
  cardEmpty.strokeWeight = 1;
  cardEmpty.paddingLeft = 16;
  cardEmpty.paddingRight = 16;
  cardEmpty.paddingTop = 16;
  cardEmpty.paddingBottom = 16;
  cardEmpty.appendChild(makeBadge("W-06: Rỗng", C.bgSubtle, C.textMuted));
  cardEmpty.appendChild(createText("Chưa có khoá học", 16, FONT_SEMI, C.text));
  cardEmpty.appendChild(createText("Bạn chưa bắt đầu khoá học nào. Hãy tải giáo trình để WayFinder dựng lộ trình học tập thông minh.", 12, FONT_REG, C.textMuted));
  const btnUploadDoc = makeButton("+ Tải giáo trình mới", C.surface, C.primary, C.primary);
  btnUploadDoc.resize(256, 44);
  cardEmpty.appendChild(btnUploadDoc);
  w06CardsRow.appendChild(cardEmpty);

  // State 3: Loading Shimmer
  const cardLoading = figma.createFrame();
  cardLoading.layoutMode = "VERTICAL";
  cardLoading.itemSpacing = 12;
  cardLoading.resize(288, 440);
  cardLoading.cornerRadius = 12;
  cardLoading.fills = solidFill(C.bgSubtle);
  cardLoading.strokes = [{ type: "SOLID", color: C.border }];
  cardLoading.strokeWeight = 1;
  cardLoading.paddingLeft = 16;
  cardLoading.paddingRight = 16;
  cardLoading.paddingTop = 16;
  cardLoading.paddingBottom = 16;
  cardLoading.appendChild(makeBadge("W-06: Đang tải", C.brandTint, C.brand));
  cardLoading.appendChild(createText("Đang tải dữ liệu...", 16, FONT_SEMI, C.textMuted));

  const shim1 = figma.createFrame(); shim1.resize(256, 24); shim1.cornerRadius = 6; shim1.fills = solidFill(C.border);
  const shim2 = figma.createFrame(); shim2.resize(180, 16); shim2.cornerRadius = 4; shim2.fills = solidFill(C.border);
  const shim3 = figma.createFrame(); shim3.resize(256, 44); shim3.cornerRadius = 8; shim3.fills = solidFill(C.border);
  cardLoading.appendChild(shim1);
  cardLoading.appendChild(shim2);
  cardLoading.appendChild(createText("Skeleton shimmer tuân thủ prefers-reduced-motion: ngắt chuyển động khi bật.", 11, FONT_REG, C.textMuted));
  cardLoading.appendChild(shim3);
  w06CardsRow.appendChild(cardLoading);

  // State 4: Error State
  const cardError = figma.createFrame();
  cardError.layoutMode = "VERTICAL";
  cardError.itemSpacing = 12;
  cardError.resize(288, 440);
  cardError.cornerRadius = 12;
  cardError.fills = solidFill(C.bgSubtle);
  cardError.strokes = [{ type: "SOLID", color: C.danger }];
  cardError.strokeWeight = 1;
  cardError.paddingLeft = 16;
  cardError.paddingRight = 16;
  cardError.paddingTop = 16;
  cardError.paddingBottom = 16;
  cardError.appendChild(makeBadge("W-06: Lỗi tải", C.dangerTint, C.danger));
  cardError.appendChild(createText("Không thể tải danh sách", 16, FONT_SEMI, C.danger));
  const errBox = figma.createFrame();
  errBox.resize(256, 70);
  errBox.cornerRadius = 8;
  errBox.fills = solidFill(C.dangerTint);
  errBox.paddingLeft = 10; errBox.paddingRight = 10; errBox.paddingTop = 8;
  errBox.appendChild(createText("Mã lỗi: ERR_NETWORK. Không thể kết nối đến máy chủ Gateway.", 11, FONT_REG, C.danger));
  cardError.appendChild(errBox);
  const btnRetry = makeButton("Thử lại ↻", C.danger, C.white);
  btnRetry.resize(256, 44);
  cardError.appendChild(btnRetry);
  w06CardsRow.appendChild(cardError);

  w06Frame.appendChild(w06CardsRow);
  figma.currentPage.appendChild(w06Frame);
  createdNodes.push(w06Frame);

  // ==========================================
  // 8. FRAME: MÀN HÌNH W-04 (QUẢN LÝ HỒ SƠ & PHIÊN /ho-so)
  // ==========================================
  const w04Frame = figma.createFrame();
  w04Frame.name = "8. Màn hình W-04: Quản lý Hồ sơ & Phiên (/ho-so)";
  w04Frame.x = 0;
  w04Frame.y = 3520;
  w04Frame.resize(1280, 620);
  w04Frame.fills = solidFill(C.surface);
  w04Frame.cornerRadius = 16;
  w04Frame.strokes = [{ type: "SOLID", color: C.border }];
  w04Frame.strokeWeight = 1;
  w04Frame.layoutMode = "VERTICAL";
  w04Frame.paddingTop = 28;
  w04Frame.paddingBottom = 28;
  w04Frame.paddingLeft = 32;
  w04Frame.paddingRight = 32;
  w04Frame.itemSpacing = 20;

  w04Frame.appendChild(createText("Hồ sơ học viên & Bảo mật phiên (/ho-so) — W-04", 22, FONT_BOLD, C.text));
  w04Frame.appendChild(createText("Thông tin cá nhân, Đổi mật khẩu Argon2id và Quản lý/Thu hồi phiên đăng nhập chủ động.", 13, FONT_REG, C.textMuted));

  const w04CardsRow = figma.createFrame();
  w04CardsRow.layoutMode = "HORIZONTAL";
  w04CardsRow.itemSpacing = 20;
  w04CardsRow.fills = [];

  // Card 1: User Profile Info
  const profCard = figma.createFrame();
  profCard.layoutMode = "VERTICAL";
  profCard.itemSpacing = 12;
  profCard.resize(380, 460);
  profCard.cornerRadius = 12;
  profCard.fills = solidFill(C.bgSubtle);
  profCard.strokes = [{ type: "SOLID", color: C.border }];
  profCard.strokeWeight = 1;
  profCard.paddingLeft = 20; profCard.paddingRight = 20; profCard.paddingTop = 20; profCard.paddingBottom = 20;
  profCard.appendChild(makeBadge("W-04: Thông tin", C.brandTint, C.primary));
  profCard.appendChild(createText("Hồ sơ cá nhân", 18, FONT_BOLD, C.text));
  profCard.appendChild(createText("Email: user@example.com", 14, FONT_SEMI, C.text));
  profCard.appendChild(createText("Trạng thái email: ✓ Đã xác minh", 13, FONT_REG, C.success));
  profCard.appendChild(createText("Vai trò: Học viên chuẩn (Member)", 13, FONT_REG, C.textMuted));
  profCard.appendChild(createText("Ngày tham gia: 2026-10-15", 13, FONT_REG, C.textMuted));
  w04CardsRow.appendChild(profCard);

  // Card 2: Change Password (Argon2id)
  const passCard = figma.createFrame();
  passCard.layoutMode = "VERTICAL";
  passCard.itemSpacing = 10;
  passCard.resize(380, 460);
  passCard.cornerRadius = 12;
  passCard.fills = solidFill(C.bgSubtle);
  passCard.strokes = [{ type: "SOLID", color: C.border }];
  passCard.strokeWeight = 1;
  passCard.paddingLeft = 20; passCard.paddingRight = 20; passCard.paddingTop = 20; passCard.paddingBottom = 20;
  passCard.appendChild(makeBadge("W-04: Bảo mật", C.accentTint, C.accentText));
  passCard.appendChild(createText("Đổi mật khẩu (Argon2id)", 18, FONT_BOLD, C.text));
  passCard.appendChild(makeInput("Mật khẩu hiện tại", "••••••••••••"));
  passCard.appendChild(makeInput("Mật khẩu mới (≥8 ký tự)", "••••••••••••"));
  passCard.appendChild(makeInput("Nhập lại mật khẩu mới", "••••••••••••"));
  const btnUpdatePassW04 = makeButton("Cập nhật mật khẩu", C.primary, C.white);
  btnUpdatePassW04.resize(340, 44);
  passCard.appendChild(btnUpdatePassW04);
  w04CardsRow.appendChild(passCard);

  // Card 3: Session Management
  const sessCard = figma.createFrame();
  sessCard.layoutMode = "VERTICAL";
  sessCard.itemSpacing = 12;
  sessCard.resize(380, 460);
  sessCard.cornerRadius = 12;
  sessCard.fills = solidFill(C.bgSubtle);
  sessCard.strokes = [{ type: "SOLID", color: C.border }];
  sessCard.strokeWeight = 1;
  sessCard.paddingLeft = 20; sessCard.paddingRight = 20; sessCard.paddingTop = 20; sessCard.paddingBottom = 20;
  sessCard.appendChild(makeBadge("W-04: Phiên hoạt động", C.brandTint, C.primary));
  sessCard.appendChild(createText("Quản lý phiên đăng nhập", 18, FONT_BOLD, C.text));
  sessCard.appendChild(createText("Thiết bị hiện tại: Chrome Windows · 127.0.0.1", 13, FONT_SEMI, C.text));
  const btnLogoutCur = makeButton("Đăng xuất thiết bị này (#btn-logout-current)", C.surface, C.text, C.borderInput);
  btnLogoutCur.resize(340, 44);
  sessCard.appendChild(btnLogoutCur);
  sessCard.appendChild(createText("Các phiên khác: 1 thiết bị di động (Safari iPhone)", 13, FONT_REG, C.textMuted));
  const btnLogoutAll = makeButton("Đăng xuất tất cả thiết bị khác (#btn-logout-all)", C.danger, C.white);
  btnLogoutAll.resize(340, 44);
  sessCard.appendChild(btnLogoutAll);
  w04CardsRow.appendChild(sessCard);

  w04Frame.appendChild(w04CardsRow);
  figma.currentPage.appendChild(w04Frame);
  createdNodes.push(w04Frame);

  // ==========================================
  // 9. FRAME: MÀN HÌNH W-07 (LỘ TRÌNH & TIẾN ĐỘ BÀI HỌC)
  // ==========================================
  const w07Frame = figma.createFrame();
  w07Frame.name = "9. Màn hình W-07: Lộ trình & Quản lý Tiến độ (/khoa-hoc/:cid)";
  w07Frame.x = 0;
  w07Frame.y = 4160;
  w07Frame.resize(1280, 620);
  w07Frame.fills = solidFill(C.surface);
  w07Frame.cornerRadius = 16;
  w07Frame.strokes = [{ type: "SOLID", color: C.border }];
  w07Frame.strokeWeight = 1;
  w07Frame.layoutMode = "VERTICAL";
  w07Frame.paddingTop = 28;
  w07Frame.paddingBottom = 28;
  w07Frame.paddingLeft = 32;
  w07Frame.paddingRight = 32;
  w07Frame.itemSpacing = 16;

  w07Frame.appendChild(createText("Lộ trình học tập & Quản lý Tiến độ bài học — W-07", 22, FONT_BOLD, C.text));
  w07Frame.appendChild(createText("Mã tài liệu: DOC-SAMPLE-01 · Module mở/gập, tiến độ trực quan, đánh dấu hoàn thành và hoàn tác bài học (0 USD chi phí học viên).", 13, FONT_REG, C.textMuted));

  const w07CardsRow = figma.createFrame();
  w07CardsRow.layoutMode = "HORIZONTAL";
  w07CardsRow.itemSpacing = 16;
  w07CardsRow.fills = [];

  // Card 1: Module 1 Completed
  const m1Card = figma.createFrame();
  m1Card.layoutMode = "VERTICAL";
  m1Card.itemSpacing = 12;
  m1Card.resize(380, 460);
  m1Card.cornerRadius = 12;
  m1Card.fills = solidFill(C.bgSubtle);
  m1Card.strokes = [{ type: "SOLID", color: C.success }];
  m1Card.strokeWeight = 2;
  m1Card.paddingLeft = 20; m1Card.paddingRight = 20; m1Card.paddingTop = 20; m1Card.paddingBottom = 20;
  m1Card.appendChild(makeBadge("Module 1 · Xong 5/5", C.successTint, C.success));
  m1Card.appendChild(createText("① Giải phẫu Đại thể Tim", 18, FONT_BOLD, C.text));
  m1Card.appendChild(createText("Hình thể ngoài, rãnh liên thất, 4 buồng tim và hệ thống vách ngăn.", 13, FONT_REG, C.textMuted));
  m1Card.appendChild(createText("Tiến độ: 5/5 bài học (100% hoàn thành)", 13, FONT_SEMI, C.success));
  const btnRevM1 = makeButton("Xem lại bài học", C.surface, C.text, C.borderInput);
  btnRevM1.resize(340, 44);
  m1Card.appendChild(btnRevM1);
  w07CardsRow.appendChild(m1Card);

  // Card 2: Module 2 In Progress with Concept Accordion
  const m2Card = figma.createFrame();
  m2Card.layoutMode = "VERTICAL";
  m2Card.itemSpacing = 10;
  m2Card.resize(400, 460);
  m2Card.cornerRadius = 12;
  m2Card.fills = solidFill(C.bgSubtle);
  m2Card.strokes = [{ type: "SOLID", color: C.primary }];
  m2Card.strokeWeight = 2;
  m2Card.paddingLeft = 20; m2Card.paddingRight = 20; m2Card.paddingTop = 20; m2Card.paddingBottom = 20;
  m2Card.appendChild(makeBadge("Module 2 · Đang học 3/8", C.accentTint, C.accentText));
  m2Card.appendChild(createText("② Động mạch Vành & Tuần hoàn", 18, FONT_BOLD, C.text));
  
  // Concept item A (Learned + Rollback)
  const cItemA = figma.createFrame();
  cItemA.layoutMode = "HORIZONTAL";
  cItemA.primaryAxisAlignItems = "SPACE_BETWEEN";
  cItemA.counterAxisAlignItems = "CENTER";
  cItemA.resize(360, 48);
  cItemA.cornerRadius = 8;
  cItemA.fills = solidFill(C.successTint);
  cItemA.paddingLeft = 10; cItemA.paddingRight = 10;
  cItemA.appendChild(createText("■ Nhánh LAD (✓ Đã học)", 12, FONT_SEMI, C.success));
  const btnRollback = makeButton("Hoàn tác", C.surface, C.danger, C.danger);
  btnRollback.resize(70, 32);
  cItemA.appendChild(btnRollback);
  m2Card.appendChild(cItemA);

  // Concept item B (Not learned + Mark complete)
  const cItemB = figma.createFrame();
  cItemB.layoutMode = "HORIZONTAL";
  cItemB.primaryAxisAlignItems = "SPACE_BETWEEN";
  cItemB.counterAxisAlignItems = "CENTER";
  cItemB.resize(360, 48);
  cItemB.cornerRadius = 8;
  cItemB.fills = solidFill(C.surface);
  cItemB.strokes = [{ type: "SOLID", color: C.border }];
  cItemB.paddingLeft = 10; cItemB.paddingRight = 10;
  cItemB.appendChild(createText("□ Nhánh LCx (Chưa học)", 12, FONT_REG, C.text));
  const btnMark = makeButton("Đánh dấu", C.primary, C.white);
  btnMark.resize(76, 32);
  cItemB.appendChild(btnMark);
  m2Card.appendChild(cItemB);

  const btnContM2 = makeButton("Tiếp tục học Module 2 ➔", C.primary, C.white);
  btnContM2.resize(360, 44);
  m2Card.appendChild(btnContM2);
  w07CardsRow.appendChild(m2Card);

  // Card 3: Action & Quiz Panel
  const actCard = figma.createFrame();
  actCard.layoutMode = "VERTICAL";
  actCard.itemSpacing = 12;
  actCard.resize(380, 460);
  actCard.cornerRadius = 12;
  actCard.fills = solidFill(C.bgSubtle);
  actCard.strokes = [{ type: "SOLID", color: C.border }];
  actCard.strokeWeight = 1;
  actCard.paddingLeft = 20; actCard.paddingRight = 20; actCard.paddingTop = 20; actCard.paddingBottom = 20;
  actCard.appendChild(makeBadge("Hoạt động tổng kết", C.brandTint, C.primary));
  actCard.appendChild(createText("Lượng giá & Tài liệu", 18, FONT_BOLD, C.text));
  actCard.appendChild(createText("Làm bài kiểm tra trắc nghiệm cả khoá hoặc tạo tài liệu bài học rút gọn.", 13, FONT_REG, C.textMuted));
  const btnQuiz = makeButton("📝 Làm quiz cả khoá", C.primary, C.white);
  btnQuiz.resize(340, 44);
  actCard.appendChild(btnQuiz);
  const btnShare = makeButton("🔗 Chia sẻ liên kết mời", C.surface, C.text, C.borderInput);
  btnShare.resize(340, 44);
  actCard.appendChild(btnShare);
  w07CardsRow.appendChild(actCard);

  w07Frame.appendChild(w07CardsRow);
  figma.currentPage.appendChild(w07Frame);
  createdNodes.push(w07Frame);

  // ==========================================
  // 10. FRAME: MÀN HÌNH W-14 (TẢI GIÁO TRÌNH & DỰNG LỘ TRÌNH 4 BƯỚC)
  // ==========================================
  const w14Frame = figma.createFrame();
  w14Frame.name = "10. Màn hình W-14: Tải giáo trình & Dựng lộ trình (/tai-len)";
  w14Frame.x = 0;
  w14Frame.y = 4800;
  w14Frame.resize(1280, 620);
  w14Frame.fills = solidFill(C.surface);
  w14Frame.cornerRadius = 16;
  w14Frame.strokes = [{ type: "SOLID", color: C.border }];
  w14Frame.strokeWeight = 1;
  w14Frame.layoutMode = "VERTICAL";
  w14Frame.paddingTop = 28;
  w14Frame.paddingBottom = 28;
  w14Frame.paddingLeft = 32;
  w14Frame.paddingRight = 32;
  w14Frame.itemSpacing = 16;

  w14Frame.appendChild(createText("Tải tài liệu & Dựng lộ trình 4 bước — W-14", 22, FONT_BOLD, C.text));
  w14Frame.appendChild(createText("Chọn tệp PDF/DOCX, xác nhận bản quyền, tiến trình 4 bước và xử lý cảnh báo bản quét (0 USD chi phí học viên).", 13, FONT_REG, C.textMuted));

  const w14CardsRow = figma.createFrame();
  w14CardsRow.layoutMode = "HORIZONTAL";
  w14CardsRow.itemSpacing = 16;
  w14CardsRow.fills = [];

  // Card 1: Upload & Copyright
  const upCard = figma.createFrame();
  upCard.layoutMode = "VERTICAL";
  upCard.itemSpacing = 12;
  upCard.resize(380, 460);
  upCard.cornerRadius = 12;
  upCard.fills = solidFill(C.bgSubtle);
  upCard.strokes = [{ type: "SOLID", color: C.border }];
  upCard.paddingLeft = 20; upCard.paddingRight = 20; upCard.paddingTop = 20; upCard.paddingBottom = 20;
  upCard.appendChild(makeBadge("Bước 1: Chọn tài liệu", C.brandTint, C.primary));
  upCard.appendChild(createText("Chọn giáo trình PDF/DOCX", 18, FONT_BOLD, C.text));
  upCard.appendChild(createText("Tệp đã chọn: DOC-SAMPLE-01.pdf (8.4 MB)", 13, FONT_SEMI, C.text));
  upCard.appendChild(createText("☑ Tôi có quyền dùng và chia sẻ tài liệu này", 12, FONT_REG, C.text));
  const btnStartPipeline = makeButton("🚀 Dựng lộ trình", C.primary, C.white);
  btnStartPipeline.resize(340, 44);
  upCard.appendChild(btnStartPipeline);
  w14CardsRow.appendChild(upCard);

  // Card 2: 4-Step Build Progress
  const progCard = figma.createFrame();
  progCard.layoutMode = "VERTICAL";
  progCard.itemSpacing = 10;
  progCard.resize(380, 460);
  progCard.cornerRadius = 12;
  progCard.fills = solidFill(C.bgSubtle);
  progCard.strokes = [{ type: "SOLID", color: C.primary }];
  progCard.strokeWeight = 2;
  progCard.paddingLeft = 20; progCard.paddingRight = 20; progCard.paddingTop = 20; progCard.paddingBottom = 20;
  progCard.appendChild(makeBadge("Bước 2: Tiến trình 4 bước", C.brandTint, C.primary));
  progCard.appendChild(createText("Đang dựng lộ trình thông minh", 18, FONT_BOLD, C.text));
  progCard.appendChild(createText("✓ 1. Đọc tài liệu (Trích văn bản & mục lục)", 12, FONT_SEMI, C.success));
  progCard.appendChild(createText("● 2. Trích khái niệm (Nhận diện thực thể)", 12, FONT_SEMI, C.primary));
  progCard.appendChild(createText("○ 3. Dựng đồ thị và lộ trình", 12, FONT_REG, C.textMuted));
  progCard.appendChild(createText("○ 4. Chuẩn bị bài học", 12, FONT_REG, C.textMuted));
  const btnCancelProg = makeButton("Huỷ tiến trình", C.surface, C.danger, C.danger);
  btnCancelProg.resize(340, 44);
  progCard.appendChild(btnCancelProg);
  w14CardsRow.appendChild(progCard);

  // Card 3: Scanned PDF Error Handling
  const errCard = figma.createFrame();
  errCard.layoutMode = "VERTICAL";
  errCard.itemSpacing = 12;
  errCard.resize(380, 460);
  errCard.cornerRadius = 12;
  errCard.fills = solidFill(C.bgSubtle);
  errCard.strokes = [{ type: "SOLID", color: C.danger }];
  errCard.strokeWeight = 2;
  errCard.paddingLeft = 20; errCard.paddingRight = 20; errCard.paddingTop = 20; errCard.paddingBottom = 20;
  errCard.appendChild(makeBadge("Lỗi: Bản quét (Scanned PDF)", C.dangerTint, C.danger));
  errCard.appendChild(createText("Tài liệu không hợp lệ", 18, FONT_BOLD, C.danger));
  const scanErrBox = figma.createFrame();
  scanErrBox.resize(340, 80);
  scanErrBox.cornerRadius = 8;
  scanErrBox.fills = solidFill(C.dangerTint);
  scanErrBox.paddingLeft = 12; scanErrBox.paddingRight = 12; scanErrBox.paddingTop = 10;
  scanErrBox.appendChild(createText("⚠️ Tệp này là bản quét (ảnh chụp trang), WayFinder chưa đọc được. Hãy dùng bản PDF có chữ chọn được.", 12, FONT_REG, C.danger));
  errCard.appendChild(scanErrBox);
  errCard.appendChild(createText("Lưu ý: Không trừ lượt và không phát sinh bất kỳ chi phí nào.", 11, FONT_REG, C.textMuted));
  const btnRetryUpload = makeButton("Thử lại với tệp khác", C.primary, C.white);
  btnRetryUpload.resize(340, 44);
  errCard.appendChild(btnRetryUpload);
  w14CardsRow.appendChild(errCard);

  w14Frame.appendChild(w14CardsRow);
  figma.currentPage.appendChild(w14Frame);
  createdNodes.push(w14Frame);

  // ==========================================
  // 11. FRAME: MÀN HÌNH W-11 (QUẢN LÝ KHOÁ HỌC & CHIA SẺ LIÊN KẾT)
  // ==========================================
  const w11Frame = figma.createFrame();
  w11Frame.name = "11. Màn hình W-11: Quản lý Khoá học & Chia sẻ Liên kết (/join)";
  w11Frame.x = 0;
  w11Frame.y = 5450;
  w11Frame.resize(1280, 540);
  w11Frame.fills = solidFill(C.surface);
  w11Frame.cornerRadius = 16;
  w11Frame.strokes = [{ type: "SOLID", color: C.border }];
  w11Frame.strokeWeight = 1;
  w11Frame.layoutMode = "VERTICAL";
  w11Frame.paddingTop = 28; w11Frame.paddingBottom = 28;
  w11Frame.paddingLeft = 32; w11Frame.paddingRight = 32;
  w11Frame.itemSpacing = 20;

  w11Frame.appendChild(createText("Quản lý Khoá học & Chia sẻ Liên kết (W-11 /join/:token)", 22, FONT_BOLD, C.text));
  w11Frame.appendChild(createText("Bao gồm: Cấu hình tạo link (thời hạn, số lượt), Bảng danh sách link & thu hồi, Màn hình tham gia minh bạch dữ liệu.", 13, FONT_REG, C.textMuted));

  const w11CardsRow = figma.createFrame();
  w11CardsRow.layoutMode = "HORIZONTAL";
  w11CardsRow.itemSpacing = 16;
  w11CardsRow.fills = [];

  // Card 1: Course Share Settings
  const w11ShareCard = figma.createFrame();
  w11ShareCard.layoutMode = "VERTICAL";
  w11ShareCard.itemSpacing = 12;
  w11ShareCard.resize(380, 420);
  w11ShareCard.cornerRadius = 12;
  w11ShareCard.fills = solidFill(C.bgSubtle);
  w11ShareCard.strokes = [{ type: "SOLID", color: C.border }];
  w11ShareCard.paddingLeft = 16; w11ShareCard.paddingRight = 16; w11ShareCard.paddingTop = 16; w11ShareCard.paddingBottom = 16;
  w11ShareCard.appendChild(makeBadge("W-11: Quản lý chia sẻ", C.brandTint, C.primary));
  w11ShareCard.appendChild(createText("Tạo liên kết tham gia mới", 16, FONT_SEMI, C.text));
  w11ShareCard.appendChild(createText("Thời hạn: 7 ngày • Tối đa 50 học viên", 12, FONT_REG, C.textMuted));
  const btnCreateLink = makeButton("+ Tạo liên kết mới", C.primary, C.white);
  btnCreateLink.resize(348, 44);
  w11ShareCard.appendChild(btnCreateLink);
  w11CardsRow.appendChild(w11ShareCard);

  // Card 2: Link List & Revocation
  const w11ListCard = figma.createFrame();
  w11ListCard.layoutMode = "VERTICAL";
  w11ListCard.itemSpacing = 10;
  w11ListCard.resize(380, 420);
  w11ListCard.cornerRadius = 12;
  w11ListCard.fills = solidFill(C.bgSubtle);
  w11ListCard.strokes = [{ type: "SOLID", color: C.border }];
  w11ListCard.paddingLeft = 16; w11ListCard.paddingRight = 16; w11ListCard.paddingTop = 16; w11ListCard.paddingBottom = 16;
  w11ListCard.appendChild(makeBadge("Danh sách liên kết", C.successTint, C.success));
  w11ListCard.appendChild(createText("/join/WF-PHARM-2026", 16, FONT_SEMI, C.primary));
  w11ListCard.appendChild(createText("Đã dùng: 14/50 lượt • Còn 5 ngày", 12, FONT_REG, C.textMuted));
  const btnRevokeLink = makeButton("Thu hồi liên kết", C.surface, C.danger, C.danger);
  btnRevokeLink.resize(348, 44);
  w11ListCard.appendChild(btnRevokeLink);
  w11CardsRow.appendChild(w11ListCard);

  // Card 3: Join Screen (/join/:token) with Privacy Notice
  const w11JoinCard = figma.createFrame();
  w11JoinCard.layoutMode = "VERTICAL";
  w11JoinCard.itemSpacing = 10;
  w11JoinCard.resize(380, 420);
  w11JoinCard.cornerRadius = 12;
  w11JoinCard.fills = solidFill(C.bgSubtle);
  w11JoinCard.strokes = [{ type: "SOLID", color: C.primary }];
  w11JoinCard.strokeWeight = 2;
  w11JoinCard.paddingLeft = 16; w11JoinCard.paddingRight = 16; w11JoinCard.paddingTop = 16; w11JoinCard.paddingBottom = 16;
  w11JoinCard.appendChild(makeBadge("Màn hình /join/:token", C.brandTint, C.primary));
  w11JoinCard.appendChild(createText("Xác nhận vào Dược lý lâm sàng", 16, FONT_BOLD, C.text));
  const privacyBox = figma.createFrame();
  privacyBox.resize(348, 68);
  privacyBox.cornerRadius = 8;
  privacyBox.fills = solidFill(C.brandTint);
  privacyBox.paddingLeft = 10; privacyBox.paddingRight = 10; privacyBox.paddingTop = 8;
  privacyBox.appendChild(createText("🔒 Chủ khoá thấy tên, ngày vào, số bài học. Không thấy chat hay bài làm.", 11, FONT_REG, C.primary));
  w11JoinCard.appendChild(privacyBox);
  const btnJoinConfirm = makeButton("Tham gia khoá học ➔", C.primary, C.white);
  btnJoinConfirm.resize(348, 44);
  w11JoinCard.appendChild(btnJoinConfirm);
  w11CardsRow.appendChild(w11JoinCard);

  w11Frame.appendChild(w11CardsRow);
  figma.currentPage.appendChild(w11Frame);
  createdNodes.push(w11Frame);

  // Focus and Zoom
  figma.viewport.scrollAndZoomIntoView(createdNodes);

  // Transparent Reaction Reporting
  const reactionSummary = reactionStats.failed === 0 && reactionStats.linked > 0
    ? `Đã nối thành công ${reactionStats.linked}/${reactionStats.attempted} prototype reactions.`
    : `Reactions: ${reactionStats.linked} tự động, ${reactionStats.failed} cần nối thủ công qua panel Prototype của Figma.`;
  figma.notify(`WayFinder: Đã tạo ${createdNodes.length} Khung Artboard (10 Frames chuẩn: W-02..W-14). ${reactionSummary}`);
  console.log("WayFinder Plugin Generation Report:", {
    totalFrames: createdNodes.length,
    reactions: reactionStats
  });
  figma.closePlugin();
})();
