import { LANGUAGES, getLang, setLang } from "../i18n.js";

// Nhóm nút chọn ngôn ngữ (radio). onChange(code) được gọi sau khi lưu lựa chọn.
export function mountLanguagePicker(container, onChange) {
  const draw = () => {
    container.innerHTML = LANGUAGES.map((l) => `
      <button type="button" role="radio" class="lang-chip" lang="${l.code}"
              data-code="${l.code}" aria-checked="${l.code === getLang()}">${l.label}</button>`).join("");
  };
  draw();
  container.addEventListener("click", (e) => {
    const btn = e.target.closest(".lang-chip");
    if (!btn || btn.dataset.code === getLang()) return;
    setLang(btn.dataset.code);
    draw();
    onChange?.(btn.dataset.code);
  });
}
