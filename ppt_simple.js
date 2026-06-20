
var pptx = new require("pptxgenjs")();
pptx.defineLayout({ name: "WIDE", width: 10, height: 5.625 });
pptx.layout = "WIDE";

var C = {
  dark: "1B2A4A", mid: "2C3E6B", light: "F0F4FA",
  blue: "00A3E0", teal: "00C9A7", white: "FFFFFF",
  text: "1B2A4A", gray: "6B7B8D"
};

// Slide 1: Title
var s1 = pptx.addSlide(); s1.background = { fill: C.dark };
s1.addShape(pptx.shapes.RECT, { x: 0, y: 0, w: 0.12, h: 5.625, fill: { color: C.blue } });
s1.addText("执医24项 AI-Native 智能教学评估系统", {
  x: 0.8, y: 1.2, w: 8.5, h: 2.0,
  fontSize: 36, fontFace: "Arial Black", color: C.white, bold: true
});
s1.addText("USB摄像头 + AI = 24项临床技能实时评估系统", {
  x: 0.8, y: 3.3, w: 8.5, h: 0.7,
  fontSize: 18, color: C.blue
});
s1.addText("免专用硬件 · 数据不出院 · 开源可控 · 越用越准", {
  x: 0.8, y: 4.0, w: 8.5, h: 0.5,
  fontSize: 14, color: C.gray
});

// Slide 2: Solution Overview
var s2 = pptx.addSlide(); s2.background = { fill: C.light };
s2.addText("核心架构", {
  x: 0.5, y: 0.3, w: 9, h: 0.8,
  fontSize: 28, fontFace: "Arial Black", color: C.text, bold: true
});

var steps = [
  { label: "USB摄像头", sub: "¥50", c: C.blue },
  { label: "姿态识别", sub: "33关键点", c: C.teal },
  { label: "智能评分", sub: "频率/角度/稳定性", c: "F39C12" },
  { label: "实时反馈", sub: "AI导师指导", c: "27AE60" },
  { label: "数据沉淀", sub: "成长档案", c: C.mid }
];
steps.forEach(function(s, i) {
  var x = 0.3 + i * 1.95;
  s2.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: x, y: 1.5, w: 1.7, h: 1.4, fill: { color: s.c }, rectRadius: 0.1 });
  s2.addText(s.label, { x: x, y: 1.7, w: 1.7, h: 0.5, fontSize: 16, fontFace: "Arial Black", color: C.white, bold: true, align: "center" });
  s2.addText(s.sub, { x: x, y: 2.2, w: 1.7, h: 0.5, fontSize: 11, color: C.white, align: "center" });
});

// 3 Key differentiators
var diffs = [
  { icon: "1", title: "零专用硬件", desc: "vs 传统模拟人50-200万" },
  { icon: "2", title: "数据不出院", desc: "院内部署，隐私安全" },
  { icon: "3", title: "越用越准", desc: "AI自进化引擎" }
];
diffs.forEach(function(d, i) {
  var x = 1 + i * 3;
  s2.addShape(pptx.shapes.OVAL, { x: x, y: 3.4, w: 0.45, h: 0.45, fill: { color: C.blue } });
  s2.addText(d.icon, { x: x, y: 3.4, w: 0.45, h: 0.45, fontSize: 14, color: C.white, bold: true, align: "center", valign: "middle" });
  s2.addText(d.title, { x: x + 0.6, y: 3.3, w: 2.5, h: 0.35, fontSize: 13, fontFace: "Arial Black", color: C.text, bold: true });
  s2.addText(d.desc, { x: x + 0.6, y: 3.65, w: 2.5, h: 0.3, fontSize: 11, color: C.gray });
});

s2.addText("开箱即用：pip install → 下载模型 → 插上摄像头 → 开始训练", {
  x: 0.5, y: 4.4, w: 9, h: 0.5,
  fontSize: 14, color: C.blue, italic: true
});

s2.addText("当前已实现8/24项技能：CPR、缝合打结、穿刺(3项)、导尿、气管插管、心肺叩诊、无菌术", {
  x: 0.5, y: 4.9, w: 9, h: 0.4,
  fontSize: 12, color: C.gray
});

// Slide 3: Skills Coverage
var s3 = pptx.addSlide(); s3.background = { fill: C.light };
s3.addText("当前覆盖技能 (8/24)", {
  x: 0.5, y: 0.3, w: 9, h: 0.8,
  fontSize: 28, fontFace: "Arial Black", color: C.text, bold: true
});

var cats = [
  { title: "急救 (3项)", c: "E74C3C", skills: ["心肺复苏 (CPR) ✅", "气管插管术 ✅", "除颤术"] },
  { title: "外科 (2项)", c: "F39C12", skills: ["缝合打结 ✅", "无菌术 ✅"] },
  { title: "穿刺 (3项)", c: "27AE60", skills: ["胸腔穿刺术 ✅", "腰椎穿刺术 ✅", "腹腔穿刺术"] },
  { title: "体格检查 (1项)", c: C.blue, skills: ["心肺叩诊 ✅", "腹部触诊", "神经系统检查"] },
  { title: "操作 (1项)", c: C.teal, skills: ["导尿术 ✅", "胃管置入", "静脉穿刺"] }
];

cats.forEach(function(cat, i) {
  var x = 0.3 + (i % 3) * 3.2;
  var y = 1.3 + Math.floor(i / 3) * 2.3;
  s3.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: x, y: y, w: 3.0, h: 2.0, fill: { color: C.white }, rectRadius: 0.1 });
  s3.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: x, y: y, w: 3.0, h: 0.5, fill: { color: cat.c }, rectRadius: 0.1 });
  s3.addText(cat.title, { x: x, y: y, w: 3.0, h: 0.5, fontSize: 13, fontFace: "Arial Black", color: C.white, bold: true, align: "center", valign: "middle" });
  cat.skills.forEach(function(sk, j) {
    s3.addText("• " + sk, { x: x + 0.2, y: y + 0.55 + j * 0.35, w: 2.6, h: 0.35, fontSize: 10, color: C.text });
  });
});

// Slide 4: Comparison
var s4 = pptx.addSlide(); s4.background = { fill: C.light };
s4.addText("与现有方案对比", {
  x: 0.5, y: 0.3, w: 9, h: 0.8,
  fontSize: 28, fontFace: "Arial Black", color: C.text, bold: true
});

var cols = [
  { title: "传统模拟人", items: ["硬件50-200万/台", "无AI评分", "无数据沉淀"], h: false },
  { title: "在线课程平台", items: ["仅课程内容", "无操作评估", "培训效果不可量化"], h: false },
  { title: "我们的系统 .", items: ["USB摄像头 50", "AI实时评分+导师", "全数据 + 自进化"], h: true }
];

cols.forEach(function(col, i) {
  var x = 0.4 + i * 3.2;
  s4.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: x, y: 1.3, w: 3.0, h: 0.6, fill: { color: col.h ? C.blue : C.mid }, rectRadius: 0.08 });
  s4.addText(col.title, { x: x, y: 1.3, w: 3.0, h: 0.6, fontSize: 14, fontFace: "Arial Black", color: C.white, bold: true, align: "center", valign: "middle" });
  col.items.forEach(function(item, j) {
    var bg = col.h ? C.white : C.light;
    s4.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: x, y: 2.1 + j * 0.65, w: 3.0, h: 0.55, fill: { color: bg }, line: { color: col.h ? C.blue : "ddd", width: 1 }, rectRadius: 0.05 });
    var prefix = col.h ? ". " : "x ";
    s4.addText(prefix + item, { x: x + 0.15, y: 2.1 + j * 0.65, w: 2.7, h: 0.55, fontSize: 11, color: col.h ? "27AE60" : "E74C3C", valign: "middle" });
  });
});

s4.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 0.5, y: 4.2, w: 9, h: 0.7, fill: { color: C.blue }, rectRadius: 0.08 });
s4.addText("我们的核心差异：开源(MIT)、零专用硬件、支持联邦学习、数据不出院", {
  x: 0.7, y: 4.2, w: 8.6, h: 0.7,
  fontSize: 13, color: C.white, align: "center", valign: "middle"
});

// Slide 5: CTA
var s5 = pptx.addSlide(); s5.background = { fill: C.dark };
s5.addShape(pptx.shapes.RECT, { x: 0, y: 0, w: 0.12, h: 5.625, fill: { color: C.blue } });
s5.addText("合作邀请：免费试点 + 联合研发", {
  x: 0.8, y: 0.8, w: 8.5, h: 1.0,
  fontSize: 32, fontFace: "Arial Black", color: C.white, bold: true
});
s5.addText("零成本 . 零风险 . 数据不出院 . 一周部署", {
  x: 0.8, y: 1.9, w: 8.5, h: 0.6,
  fontSize: 18, color: C.blue
});

var points = [
  "1. 免费试点1-2项技能，验证效果后再决定",
  "2. 零专用硬件：普通USB摄像头即可",
  "3. 全院内部部署：数据永不出院",
  "4. 开源(MIT)：无供应商锁定风险",
];

points.forEach(function(p, i) {
  var colors = [C.blue, C.teal, "F39C12", "27AE60"];
  s5.addShape(pptx.shapes.OVAL, { x: 1.2, y: 2.8 + i * 0.45, w: 0.3, h: 0.3, fill: { color: colors[i] } });
  s5.addText(p, { x: 1.7, y: 2.8 + i * 0.45, w: 7, h: 0.35, fontSize: 14, color: C.white });
});

s5.addShape(pptx.shapes.ROUNDED_RECTANGLE, { x: 2, y: 4.8, w: 6, h: 0.5, fill: { color: C.blue }, rectRadius: 0.08 });
s5.addText("keyneszeng@gmail.com  |  github.com/calmanzeng/cpr-ai-scorer", {
  x: 2, y: 4.8, w: 6, h: 0.5,
  fontSize: 12, color: C.white, align: "center", valign: "middle", bold: true
});

// Save
var outPath = "C:/Users/Administrator/Desktop/执医AI智能教学评估系统.pptx";
pptx.writeFile({ fileName: outPath })
  .then(function() { console.log("DONE: " + outPath); })
  .catch(function(e) { console.log("ERROR: " + e.message); });
