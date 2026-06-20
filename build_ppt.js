
var pptxgen = require("pptxgenjs");
var pptx = new pptxgen();

// ---- Theme ----
var C = {
    darkBg: "1B2A4A",    // deep navy
    midBg: "2C3E6B",     // medium blue
    lightBg: "F0F4FA",   // light blue-gray
    accent: "00A3E0",     // bright cyan/blue
    accent2: "00C9A7",    // teal
    white: "FFFFFF",
    text: "1B2A4A",
    gray: "6B7B8D",
    red: "E74C3C",
    green: "27AE60",
    yellow: "F39C12",
};

pptx.defineLayout({ name: "WIDE", width: 13.333, height: 7.5 });
pptx.layout = "WIDE";

// ---- Slide 1: Title ----
var s1 = pptx.addSlide();
s1.background = { fill: C.darkBg };

// Decorative elements
s1.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 0, y: 0, w: 0.15, h: 7.5, fill: { color: C.accent } });
s1.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 10.5, y: 5.5, w: 3, h: 2, fill: { color: C.midBg }, rotate: -15, rectRadius: 0.3 });
s1.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 11, y: 5.2, w: 2.5, h: 1.8, fill: { color: C.accent }, rotate: -10, rectRadius: 0.2, transparency: 80 });

// Main title
s1.addText("执医24项\nAI-Native 智能教学评估系统", {
    x: 1.5, y: 1.5, w: 8, h: 3,
    fontSize: 44, fontFace: "Arial Black", color: C.white, bold: true,
    lineSpacing: 54
});

// Subtitle
s1.addText("用AI替代考官主观评分 · USB摄像头即可 · 数据不出院 · 越用越准", {
    x: 1.5, y: 4.8, w: 8, h: 0.8,
    fontSize: 18, fontFace: "Calibri", color: C.accent
});

// Footer
s1.addText("keyneszeng@gmail.com  |  github.com/calmanzeng/cpr-ai-scorer", {
    x: 1.5, y: 6.5, w: 8, h: 0.5,
    fontSize: 12, color: C.gray
});

// ---- Slide 2: Problem ----
var s2 = pptx.addSlide();
s2.background = { fill: C.lightBg };
s2.addText("当前临床技能培训的四大痛点", {
    x: 0.8, y: 0.4, w: 10, h: 1,
    fontSize: 32, fontFace: "Arial Black", color: C.text, bold: true
});

// Pain points grid
var pains = [
    { icon: "1", title: "考官严重不足", desc: "一位主任医师只能同时带3-5个规培生\n全国1700+三甲医院，40万在培住院医\n师生比严重失衡" },
    { icon: "2", title: "评分主观不标准", desc: "同一个人换考官可能差20分\nOSCE\"客观结构化考试\"名存实亡\n不同院区标准不统一" },
    { icon: "3", title: "练习机会极少", desc: "高端模拟人50-200万/台\n耗材昂贵（缝合皮、穿刺包一次性）\n学生人均每项操作 < 3次" },
    { icon: "4", title: "数据完全浪费", desc: "操作过程没有数据沉淀\n进步曲线不可见\n教学管理看不到全院培训水平" },
];

pains.forEach(function(p, i) {
    var col = i % 2;
    var row = Math.floor(i / 2);
    var x = 0.8 + col * 6.2;
    var y = 1.8 + row * 2.7;
    
    // Card
    s2.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
        x: x, y: y, w: 5.8, h: 2.4,
        fill: { color: C.white }, shadow: { type: "outer", blur: 6, offset: 2, color: "000000", opacity: 0.1 },
        rectRadius: 0.15
    });
    
    // Number circle
    s2.addShape(pptx.shapes.OVAL, {
        x: x + 0.3, y: y + 0.3, w: 0.6, h: 0.6,
        fill: { color: C.accent }
    });
    s2.addText(p.icon, {
        x: x + 0.3, y: y + 0.3, w: 0.6, h: 0.6,
        fontSize: 20, color: C.white, bold: true, align: "center", valign: "middle"
    });
    
    // Title
    s2.addText(p.title, {
        x: x + 1.1, y: y + 0.3, w: 4.2, h: 0.5,
        fontSize: 18, fontFace: "Arial Black", color: C.text, bold: true
    });
    
    // Description
    s2.addText(p.desc, {
        x: x + 1.1, y: y + 0.9, w: 4.2, h: 1.3,
        fontSize: 13, color: C.gray, lineSpacing: 22
    });
});

// ---- Slide 3: Solution Overview ----
var s3 = pptx.addSlide();
s3.background = { fill: C.darkBg };

s3.addText("解决方案：AI替代考官主观评分", {
    x: 0.8, y: 0.4, w: 10, h: 1,
    fontSize: 32, fontFace: "Arial Black", color: C.white, bold: true
});

// Architecture boxes - horizontal flow
var archItems = [
    { label: "USB摄像头", sub: "¥50 普通摄像头", color: C.accent },
    { label: "AI姿态识别", sub: "MediaPipe 33关键点", color: C.accent2 },
    { label: "智能评分", sub: "频率/节奏/深度/规范", color: C.yellow },
    { label: "实时反馈", sub: "AI导师 + HUD面板", color: C.green },
    { label: "数据沉淀", sub: "成长档案 + 管理看板", color: C.accent },
];

archItems.forEach(function(item, i) {
    var x = 0.5 + i * 2.5;
    var y = 2.0;
    
    s3.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
        x: x, y: y, w: 2.2, h: 1.8,
        fill: { color: item.color },
        rectRadius: 0.15
    });
    
    s3.addText(item.label, {
        x: x, y: y + 0.3, w: 2.2, h: 0.6,
        fontSize: 20, fontFace: "Arial Black", color: C.white, bold: true, align: "center"
    });
    s3.addText(item.sub, {
        x: x, y: y + 1.0, w: 2.2, h: 0.6,
        fontSize: 12, color: C.white, align: "center"
    });
    
    // Arrow between boxes
    if (i < 4) {
        s3.addText("→", {
            x: x + 2.2, y: y + 0.5, w: 0.4, h: 0.8,
            fontSize: 28, color: C.white, align: "center", valign: "middle"
        });
    }
});

// Key differentiators at bottom
var diffs = [
    { label: "零专用硬件", sub: "vs 传统模拟人50-200万" },
    { label: "数据不出院", sub: "全院内部部署" },
    { label: "开源可控", sub: "MIT协议，无供应商锁定" },
    { label: "越用越准", sub: "内置自进化AI引擎" },
];

diffs.forEach(function(d, i) {
    var x = 1.5 + i * 2.8;
    s3.addShape(pptx.shapes.OVAL, {
        x: x, y: 4.5, w: 0.5, h: 0.5, fill: { color: C.accent }
    });
    s3.addText("✓", {
        x: x, y: 4.5, w: 0.5, h: 0.5,
        fontSize: 16, color: C.white, bold: true, align: "center", valign: "middle"
    });
    s3.addText(d.label, {
        x: x + 0.7, y: 4.4, w: 2.0, h: 0.4,
        fontSize: 14, fontFace: "Arial Black", color: C.white, bold: true
    });
    s3.addText(d.sub, {
        x: x + 0.7, y: 4.8, w: 2.0, h: 0.3,
        fontSize: 10, color: C.gray
    });
});

// ---- Slide 4: Scoring Example (CPR) ----
var s4 = pptx.addSlide();
s4.background = { fill: C.lightBg };
s4.addText("实时评分演示：心肺复苏(CPR)", {
    x: 0.8, y: 0.4, w: 10, h: 1,
    fontSize: 32, fontFace: "Arial Black", color: C.text, bold: true
});

// Left: Camera area simulation
s4.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 0.8, y: 1.6, w: 6.5, h: 5.2,
    fill: { color: C.darkBg }, rectRadius: 0.15
});
s4.addText("📹 摄像头画面", {
    x: 0.8, y: 1.8, w: 6.5, h: 0.5,
    fontSize: 14, color: C.gray, align: "center"
});

// Simulated person + skeleton
s4.addText("○", {
    x: 3.5, y: 3.2, w: 1, h: 1,
    fontSize: 72, color: C.accent, align: "center"
});
s4.addText("真人操作 + AI姿态识别叠加", {
    x: 1, y: 5.5, w: 6, h: 0.5,
    fontSize: 12, color: C.gray, align: "center"
});

// Right: Score panel
s4.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 7.8, y: 1.6, w: 4.8, h: 5.2,
    fill: { color: C.white }, shadow: { type: "outer", blur: 8, offset: 2, opacity: 0.1 },
    rectRadius: 0.15
});

// Score
s4.addText("92", {
    x: 8.2, y: 1.9, w: 2, h: 1.2,
    fontSize: 56, fontFace: "Arial Black", color: C.green, bold: true
});
s4.addText("/100", {
    x: 10.5, y: 2.3, w: 1, h: 0.6,
    fontSize: 18, color: C.gray
});

// Grade badge
s4.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 11.5, y: 2.0, w: 0.7, h: 0.7,
    fill: { color: C.green }, rectRadius: 0.1
});
s4.addText("A", {
    x: 11.5, y: 2.0, w: 0.7, h: 0.7,
    fontSize: 24, fontFace: "Arial Black", color: C.white, align: "center", valign: "middle"
});

// Metrics
var metrics = [
    { label: "按压频率", value: "108 CPM", ok: true },
    { label: "节奏一致性", value: "6.5%", ok: true },
    { label: "深度指数", value: "0.152", ok: true },
    { label: "检测次数", value: "28", ok: true },
];

metrics.forEach(function(m, i) {
    var y = 3.3 + i * 0.6;
    s4.addText(m.label, {
        x: 8.2, y: y, w: 1.8, h: 0.4,
        fontSize: 12, color: C.gray
    });
    s4.addText(m.value, {
        x: 10.2, y: y, w: 2, h: 0.4,
        fontSize: 14, color: m.ok ? C.green : C.red, fontFace: "Arial Black", bold: true
    });
});

// AI Feedback
s4.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 8.2, y: 5.9, w: 4, h: 0.6,
    fill: { color: C.accent }, rectRadius: 0.1, transparency: 80
});
s4.addText("AI: 频率正常，节奏稳定，继续保持！", {
    x: 8.3, y: 5.9, w: 3.8, h: 0.6,
    fontSize: 11, color: C.accent, italic: true
});

// ---- Slide 5: 24 Skills Coverage ----
var s5 = pptx.addSlide();
s5.background = { fill: C.lightBg };
s5.addText("覆盖24项临床技能", {
    x: 0.8, y: 0.4, w: 10, h: 1,
    fontSize: 32, fontFace: "Arial Black", color: C.text, bold: true
});

// Three columns for three exam stations
var stations = [
    {
        title: "第一站", sub: "病史采集 + 病例分析",
        skills: ["病史采集", "病例分析"],
        color: C.accent, status: "规划中 (LLM)"
    },
    {
        title: "第二站", sub: "体格检查",
        skills: ["一般检查", "头颈部检查", "胸部检查", "腹部检查", "神经系统", "脊柱四肢", "心肺叩诊", "腹部触诊"],
        color: C.yellow, status: "8项开发中"
    },
    {
        title: "第三站", sub: "基本操作",
        skills: ["CPR ✅", "缝合打结", "穿刺术", "气管插管", "导尿术", "胃管置入", "静脉穿刺", "清创术", "骨折固定", "无菌术", "换药术", "吸氧术", "吸痰术", "除颤术"],
        color: C.green, status: "1/14 已实现"
    },
];

stations.forEach(function(st, col) {
    var x = 0.5 + col * 4.2;
    
    // Header
    s5.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
        x: x, y: 1.5, w: 3.8, h: 1.0,
        fill: { color: st.color }, rectRadius: 0.1
    });
    s5.addText(st.title, {
        x: x, y: 1.5, w: 3.8, h: 0.55,
        fontSize: 22, fontFace: "Arial Black", color: C.white, bold: true, align: "center"
    });
    s5.addText(st.sub, {
        x: x, y: 2.0, w: 3.8, h: 0.4,
        fontSize: 12, color: C.white, align: "center"
    });
    
    // Skills list
    st.skills.forEach(function(skill, i) {
        s5.addText(skill, {
            x: x + 0.3, y: 2.8 + i * 0.38, w: 3.2, h: 0.35,
            fontSize: 11, color: C.text, bullet: true
        });
    });
    
    // Status badge
    var lastY = 2.8 + st.skills.length * 0.38 + 0.2;
    s5.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
        x: x + 0.3, y: lastY, w: 2.8, h: 0.4,
        fill: { color: st.color }, rectRadius: 0.08, transparency: 80
    });
    s5.addText(st.status, {
        x: x + 0.3, y: lastY, w: 2.8, h: 0.4,
        fontSize: 10, color: C.text, align: "center", valign: "middle", italic: true
    });
});

// ---- Slide 6: Self-Evolution ----
var s6 = pptx.addSlide();
s6.background = { fill: C.darkBg };
s6.addText("AI自进化：越用越准", {
    x: 0.8, y: 0.4, w: 10, h: 1,
    fontSize: 32, fontFace: "Arial Black", color: C.white, bold: true
});

var evolveStages = [
    { time: "部署1个月", title: "基础AI评分", desc: "离线模式即可运行\n无需联网，数据不出院", color: C.accent },
    { time: "部署3个月", title: "自动参数优化", desc: "积累操作数据\n评分阈值自动校准", color: C.accent2 },
    { time: "部署6个月", title: "个性化AI导师", desc: "识别个人薄弱环节\n针对性教学指导", color: C.green },
    { time: "部署12个月", title: "模型持续进化", desc: "联邦学习聚合全院数据\n准确率接近专家水平", color: C.yellow },
];

evolveStages.forEach(function(stage, i) {
    var x = 0.5 + i * 3.2;
    
    // Connecting line
    if (i < 3) {
        s6.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
            x: x + 2.9, y: 3.45, w: 0.6, h: 0.06,
            fill: { color: C.gray },
            rectRadius: 0.01
        });
    }
    
    // Circle
    s6.addShape(pptx.shapes.OVAL, {
        x: x + 1.0, y: 2.0, w: 1.2, h: 1.2,
        fill: { color: stage.color }
    });
    s6.addText(stage.time, {
        x: x + 1.0, y: 2.0, w: 1.2, h: 1.2,
        fontSize: 10, color: C.white, bold: true, align: "center", valign: "middle"
    });
    
    // Card
    s6.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
        x: x + 0.2, y: 3.8, w: 2.8, h: 2.2,
        fill: { color: C.midBg }, rectRadius: 0.15
    });
    s6.addText(stage.title, {
        x: x + 0.4, y: 4.0, w: 2.4, h: 0.5,
        fontSize: 16, fontFace: "Arial Black", color: C.white, bold: true
    });
    s6.addText(stage.desc, {
        x: x + 0.4, y: 4.6, w: 2.4, h: 1.2,
        fontSize: 12, color: C.gray, lineSpacing: 20
    });
});

// Key principle at bottom
s6.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 2.5, y: 6.5, w: 8.3, h: 0.5,
    fill: { color: C.accent }, rectRadius: 0.08, transparency: 85
});
s6.addText("隐私保护：原始视频永远不上传  |  支持联邦学习：只交换模型梯度，不交换原始数据", {
    x: 2.7, y: 6.5, w: 8, h: 0.5,
    fontSize: 12, color: C.accent, align: "center", valign: "middle"
});

// ---- Slide 7: Comparison ----
var s7 = pptx.addSlide();
s7.background = { fill: C.lightBg };
s7.addText("与现有方案对比", {
    x: 0.8, y: 0.4, w: 10, h: 1,
    fontSize: 32, fontFace: "Arial Black", color: C.text, bold: true
});

// Three columns
var cols = [
    { title: "传统模拟人厂商", items: ["硬件50-200万/台", "无AI评分", "无个性化反馈", "仅硬件，无数据"], highlight: false },
    { title: "在线课程平台", items: ["仅课程内容", "无操作评分", "无实时反馈", "无法评估实操"], highlight: false },
    { title: "我们的系统 ✨", items: ["USB摄像头 ¥50", "AI实时评分", "AI导师个性化反馈", "全维度数据 + 自进化"], highlight: true },
];

cols.forEach(function(col, i) {
    var x = 0.8 + i * 4.3;
    
    // Header
    var headerColor = col.highlight ? C.accent : C.gray;
    s7.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
        x: x, y: 1.5, w: 3.8, h: 0.8,
        fill: { color: col.highlight ? C.accent : C.midBg },
        rectRadius: 0.1
    });
    s7.addText(col.title, {
        x: x, y: 1.5, w: 3.8, h: 0.8,
        fontSize: 16, fontFace: "Arial Black", color: C.white, bold: true, align: "center", valign: "middle"
    });
    
    // Items
    col.items.forEach(function(item, j) {
        var bgColor = col.highlight ? C.white : C.lightBg;
        s7.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
            x: x, y: 2.6 + j * 0.85, w: 3.8, h: 0.7,
            fill: { color: bgColor },
            line: { color: col.highlight ? C.accent : "DDDDDD", width: 1 },
            rectRadius: 0.08
        });
        
        s7.addText((col.highlight ? "✓ " : "✗ ") + item, {
            x: x + 0.2, y: 2.6 + j * 0.85, w: 3.4, h: 0.7,
            fontSize: 12, color: col.highlight ? C.green : C.red,
            valign: "middle"
        });
    });
});

// ---- Slide 8: Deployment ----
var s8 = pptx.addSlide();
s8.background = { fill: C.lightBg };
s8.addText("部署方案与合作方式", {
    x: 0.8, y: 0.4, w: 10, h: 1,
    fontSize: 32, fontFace: "Arial Black", color: C.text, bold: true
});

// Three deployment tiers
var tiers = [
    {
        name: "免费试点", price: "¥0",
        features: ["选择1-2项技能试用", "基础AI评分功能", "单机部署", "1周安装+培训"],
        color: C.accent2
    },
    {
        name: "联合研发", price: "定制",
        features: ["共同开发专项技能模型", "贵院提供专家标注", "我们提供AI能力", "成果共享"],
        color: C.accent
    },
    {
        name: "全院部署", price: "按需",
        features: ["24项技能全覆盖", "全院数据中台", "AI导师 + 自进化引擎", "年度维护 + 持续升级"],
        color: C.midBg
    },
];

tiers.forEach(function(tier, i) {
    var x = 0.5 + i * 4.2;
    
    // Card
    s8.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
        x: x, y: 1.6, w: 3.8, h: 4.5,
        fill: { color: C.white }, shadow: { type: "outer", blur: 6, offset: 2, opacity: 0.1 },
        rectRadius: 0.15
    });
    
    // Header
    s8.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
        x: x, y: 1.6, w: 3.8, h: 1.2,
        fill: { color: tier.color }, rectRadius: 0.15
    });
    s8.addText(tier.name, {
        x: x, y: 1.7, w: 3.8, h: 0.5,
        fontSize: 20, fontFace: "Arial Black", color: C.white, bold: true, align: "center"
    });
    s8.addText(tier.price, {
        x: x, y: 2.2, w: 3.8, h: 0.4,
        fontSize: 16, color: C.white, align: "center"
    });
    
    // Features
    tier.features.forEach(function(f, j) {
        s8.addText("• " + f, {
            x: x + 0.4, y: 3.2 + j * 0.5, w: 3.0, h: 0.4,
            fontSize: 12, color: C.text, lineSpacing: 18
        });
    });
});

// ---- Slide 9: CTA ----
var s9 = pptx.addSlide();
s9.background = { fill: C.darkBg };
s9.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 0, y: 0, w: 0.15, h: 7.5, fill: { color: C.accent } });

s9.addText("邀请贵院成为首批试点单位", {
    x: 1.5, y: 1.5, w: 10, h: 1.2,
    fontSize: 40, fontFace: "Arial Black", color: C.white, bold: true
});

s9.addText("零成本 · 零风险 · 数据不出院 · 一周部署", {
    x: 1.5, y: 2.8, w: 10, h: 0.8,
    fontSize: 22, color: C.accent
});

// Key points
var ctaPoints = [
    "✓ 免费试点1-2项技能，验证效果后再决定",
    "✓ 零专用硬件：普通USB摄像头即可",
    "✓ 全院内部部署：患者数据、操作视频永不出院",
    "✓ 开源可控：MIT协议，无供应商锁定风险",
    "✓ AI自进化：使用越多，评分越精准",
];

ctaPoints.forEach(function(pt, i) {
    s9.addText(pt, {
        x: 2.0, y: 4.0 + i * 0.55, w: 9, h: 0.5,
        fontSize: 16, color: C.white
    });
});

// Contact
s9.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 3.5, y: 6.5, w: 6.3, h: 0.6,
    fill: { color: C.accent }, rectRadius: 0.1
});
s9.addText("📧 keyneszeng@gmail.com    🔗 github.com/calmanzeng/cpr-ai-scorer", {
    x: 3.5, y: 6.5, w: 6.3, h: 0.6,
    fontSize: 14, color: C.white, align: "center", valign: "middle", bold: true
});

// ---- Save ----
var outPath = "C:\\Users\\Administrator\\Desktop\\cpr_ai_scorer.pptx";
pptx.writeFile({ fileName: outPath })
    .then(function() {
        console.log("DONE: " + outPath);
    })
    .catch(function(err) {
        console.log("ERROR: " + err);
    });
