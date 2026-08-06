(() => {
  "use strict";

  function bindRemove(button) {
    button.addEventListener("click", () => {
      const row = button.closest(".row-card");
      const deleteInput = row.querySelector('input[name$="-DELETE"]');
      if (deleteInput) {
        deleteInput.value = "on";
        row.hidden = true;
      }
    });
  }

  document.querySelectorAll("[data-remove-row]").forEach(bindRemove);
  document.querySelectorAll("[data-add-row]").forEach((button) => {
    button.addEventListener("click", () => {
      const prefix = button.dataset.prefix;
      const totalInput = document.querySelector(`#id_${prefix}-TOTAL_FORMS`);
      const index = Number(totalInput.value);
      const template = document.querySelector(`#${prefix}-empty-form`);
      const container = document.querySelector(`#${prefix}-rows`);
      const wrapper = document.createElement("div");
      wrapper.innerHTML = template.innerHTML.replaceAll("__prefix__", String(index));
      const row = wrapper.firstElementChild;
      row.querySelector('input[name$="-row_id"]').value = crypto.randomUUID();
      bindRemove(row.querySelector("[data-remove-row]"));
      container.append(row);
      totalInput.value = String(index + 1);
    });
  });
})();

