/** Um ajudante mínimo para montar DOM sem innerHTML: todo texto vindo de evento entra como texto. */

type Child = Node | string | undefined | false;

export function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  props: { className?: string; title?: string; style?: string } = {},
  ...children: Child[]
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (props.className !== undefined) {
    node.className = props.className;
  }
  if (props.title !== undefined) {
    node.title = props.title;
  }
  if (props.style !== undefined) {
    node.setAttribute("style", props.style);
  }
  for (const child of children) {
    if (child !== undefined && child !== false) {
      node.append(child);
    }
  }
  return node;
}

export function button(text: string, onClick: () => void, enabled = true, active = false): HTMLButtonElement {
  const node = el("button", { className: active ? "active" : "" }, text);
  node.disabled = !enabled;
  node.addEventListener("click", onClick);
  return node;
}
