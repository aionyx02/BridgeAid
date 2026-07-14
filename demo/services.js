import { els, request } from "./core.js";

export async function loadServices() {
  els.serviceList.textContent = "載入中";
  try {
    const body = await request("/services");
    const rows = body.services.map((service) => {
      const row = document.createElement("article");
      row.className = "service-row";
      const name = document.createElement("strong");
      name.textContent = service.name;
      const meta = document.createElement("span");
      meta.className = "meta";
      meta.textContent = `${service.category} / ${service.needs_review ? "需人工確認" : "active"}`;
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = "來源";
      button.addEventListener("click", () => showSource(service.service_id));
      row.append(name, meta, button);
      return row;
    });
    els.serviceList.replaceChildren(...rows);
  } catch (error) {
    els.serviceList.textContent = `載入失敗：${error.message}`;
  }
}

export async function showSource(serviceId) {
  els.sourceDetail.textContent = "載入中";
  els.sourceDialog.showModal();
  try {
    const source = await request(`/services/${serviceId}/source`);
    const link = document.createElement("a");
    link.className = "source-link";
    link.href = source.source.url;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = source.source.url;

    const fields = [
      ["服務", source.service_name],
      ["版本", source.version],
      ["狀態", source.needs_review ? "需人工確認" : "active"],
      ["來源", source.source.title],
      ["檢查日期", source.source.last_checked_at],
    ];
    const list = document.createElement("dl");
    for (const [label, value] of fields) {
      const term = document.createElement("dt");
      term.textContent = label;
      const description = document.createElement("dd");
      description.textContent = value;
      list.append(term, description);
    }
    els.sourceDetail.replaceChildren(list, link);
  } catch (error) {
    els.sourceDetail.textContent = `載入失敗：${error.message}`;
  }
}
