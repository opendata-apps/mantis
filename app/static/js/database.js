import "../css/database.css";

const currentTable = "all_data_view";
let columnTypes = {};
let editableFields = [];
let currentPage = 1;
let itemsPerPage = 50;
let totalItems = 0;
let searchTerm = "";
let sortColumn = "meldungen_id";
let sortDirection = "asc";
let isLoading = false;
let debounceTimer;
let currentlyEditingCell = null;
let currentlyEditingCellData = null;
const editModal = document.getElementById("editModal");
let observer;
let previouslySelectedCell = null;
let sentinel = null;
let allDataLoaded = false;

// Main initialization function
function initializeApp() {
  const searchInput = document.getElementById("searchInput");
  searchInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => applySearch(searchInput.value), 300);
  });


  // Initialize search type select and clear search button
  const searchType = document.querySelector("[data-search-type]");
  if (searchType) {
    searchType.addEventListener("change", changeInputPattern);
  }

  const clearSearchBtn = document.querySelector("[data-search-clear]");
  if (clearSearchBtn) {
    clearSearchBtn.addEventListener("click", clearSearch);
  }

  // Initialize data table click handlers
  const dataTable = document.getElementById("dataTable");
  if (dataTable) {
    dataTable.addEventListener("click", function (event) {
      const cell = event.target.closest("td.editable");
      if (!cell) return;
      selectCell(cell);
    });

    dataTable.addEventListener("dblclick", function (event) {
      const cell = event.target.closest("td.editable");
      if (!cell || currentlyEditingCell) return;
      startEdit(cell);
    });
  }

  // Initialize table header click handlers
  const tableHeader = document.getElementById("tableHeader");
  if (tableHeader) {
    tableHeader.addEventListener("click", function (event) {
      const header = event.target.closest("th");
      if (!header) return;
      const column = header.getAttribute("data-column");
      toggleSortOrder(column);
    });
  }

  // Initialize edit modal buttons
  const saveEditButton = document.getElementById("saveEditButton");
  if (saveEditButton) {
    saveEditButton.addEventListener("click", function () {
      const input = document.getElementById("modalInputField");
      if (!input) return;
      const newValue = input.value;
      updateCell(
        currentlyEditingCellData.column,
        newValue,
        currentlyEditingCell
      );
      editModal.close();
    });
  }

  const cancelEditButton = document.getElementById("cancelEditButton");
  if (cancelEditButton) {
    cancelEditButton.addEventListener("click", function () {
      editModal.close();
    });
  }

  const resetEditButton = document.getElementById("resetEditButton");
  if (resetEditButton) {
    resetEditButton.addEventListener("click", function () {
      const input = document.getElementById("modalInputField");
      if (input && currentlyEditingCellData) {
        input.value = currentlyEditingCellData.originalValue;
      }
    });
  }

  // Initialize Modal (native dialog)
  if (editModal) {
    // Handle close event
    editModal.addEventListener('close', () => {
      currentlyEditingCell = null;
      currentlyEditingCellData = null;
    });
  }

  // Load initial state and data
  loadState().then(() => {
    initializeInfiniteScroll();
  });
}

// Module scripts run after parsing, so the DOM is ready.
initializeApp();

function initializeInfiniteScroll() {
  const scrollContainer = document.getElementById("scrollContainer");
  if (!scrollContainer) return;

  // Clean up old observer
  if (observer) {
    observer.disconnect();
    observer = null;
  }

  // Create new sentinel if needed
  if (!sentinel) {
    sentinel = document.createElement("div");
    sentinel.id = "scrollSentinel";
    sentinel.style.height = "1px";
  }

  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting && !isLoading && !allDataLoaded) {
        const totalPages = Math.ceil(totalItems / itemsPerPage);
        if (currentPage < totalPages) {
          currentPage++;
          fetchTableData();
        } else {
          allDataLoaded = true;
          if (observer) {
            observer.disconnect();
          }
        }
      }
    },
    {
      root: scrollContainer,
      rootMargin: "100px",
      threshold: 0.1,
    }
  );

  if (!scrollContainer.contains(sentinel)) {
    scrollContainer.appendChild(sentinel);
  }
  observer.observe(sentinel);
}

function showLoadingIndicator() {
  document.getElementById("loadingIndicator").hidden = false;
}

function hideLoadingIndicator() {
  document.getElementById("loadingIndicator").hidden = true;
}

function fetchTableData() {
  if (isLoading) return Promise.resolve();
  isLoading = true;
  showLoadingIndicator();

  const url = new URL(
    `/admin/get_table_data/${currentTable}`,
    window.location.origin
  );
  url.searchParams.append("page", currentPage);
  url.searchParams.append("per_page", itemsPerPage);
  url.searchParams.append("search", searchTerm);
  url.searchParams.append("search_type", document.getElementById("searchType").value);
  url.searchParams.append("sort_column", sortColumn);
  url.searchParams.append("sort_direction", sortDirection);

  return fetch(url)
    .then((response) => {
      if (!response.ok) throw new Error('Network response was not ok');
      return response.json();
    })
    .then((data) => {
      columnTypes = data.column_types;
      editableFields = data.editable_fields;
      totalItems = data.total_items;

      if (data.data.length === 0) {
        allDataLoaded = true;
        return;
      }

      displayTable(data.columns, data.data, currentPage === 1);
      updateSortIndicators();

      const totalPages = Math.ceil(totalItems / itemsPerPage);
      if (currentPage >= totalPages) {
        allDataLoaded = true;
      } else {
        allDataLoaded = false;
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("An error occurred while fetching data. Please try again later.");
    })
    .finally(() => {
      isLoading = false;
      hideLoadingIndicator();
    });
}

function escapeHtml(text) {
  if (text === null || text === undefined) return '';
  const div = document.createElement('div');
  div.textContent = String(text);
  return div.innerHTML;
}

function displayTable(columns, data, isNewData) {
  const tableContainer = document.getElementById("tableContainer");
  const tableTitle = document.getElementById("tableTitle");
  const tableHeader = document.getElementById("tableHeader");
  const tableBody = document.getElementById("tableBody");
  const scrollContainer = document.getElementById("scrollContainer");

  if (!scrollContainer) return;

  tableTitle.textContent = `Table: ${currentTable}`;

  if (isNewData || !tableHeader.hasChildNodes()) {
    tableHeader.innerHTML = columns
      .map(
        (col) =>
          `<th class="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-700 uppercase cursor-pointer" data-column="${col}">
            <div class="flex items-center justify-between">
              <span>${col}</span>
              <span class="ml-2 sort-indicator"></span>
            </div>
          </th>`
      )
      .join("");
  }

  const rowsHtml = data
    .map((row, rowIndex) => {
      let rowHtml = "";
      const idIndex = columns.indexOf("meldungen_id");
      const idValue = idIndex !== -1 ? row[idIndex] : null;

      row.forEach((cell, cellIndex) => {
        const columnName = columns[cellIndex];
        const cellType = columnTypes[columnName];
        const isEditable = editableFields.includes(columnName);

        let displayValue = cell;
        if (cellType === "date" && cell) {
          try {
            const date = new Date(cell);
            if (!isNaN(date.getTime())) {
              displayValue = date.toISOString().split('T')[0];
            }
          } catch {
            console.warn("Failed to format date:", cell);
          }
        }

        displayValue = escapeHtml(displayValue);

        const editableClass = isEditable
          ? "editable cursor-pointer hover:bg-gray-50"
          : "bg-gray-50 text-gray-500";

        rowHtml += `<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 ${editableClass}"
                  data-column="${columnName}"
                  data-type="${cellType}"
                  data-id-value="${escapeHtml(idValue)}"
                  tabindex="0">${displayValue}</td>`;
      });
      return `<tr class="${(tableBody.rows.length + rowIndex) % 2 === 0 ? "bg-white" : "bg-gray-50" } hover:bg-gray-100">${rowHtml}</tr>`;
    })
    .join("");

  if (isNewData) {
    tableBody.innerHTML = rowsHtml;
  } else {
    tableBody.insertAdjacentHTML("beforeend", rowsHtml);
  }

  tableContainer.classList.remove("hidden");

  // Handle sentinel after table is populated
  if (sentinel && scrollContainer.contains(sentinel)) {
    scrollContainer.removeChild(sentinel);
  }

  // Only create and append sentinel if we have more data to load
  if (!allDataLoaded) {
    if (!sentinel) {
      sentinel = document.createElement("div");
      sentinel.id = "scrollSentinel";
      sentinel.style.height = "1px";
    }
    scrollContainer.appendChild(sentinel);
  }
}

function toggleSortOrder(column) {
  // Save previous values
  const prevSortColumn = sortColumn;
  const prevSortDirection = sortDirection;

  // Update sort values
  if (sortColumn === column) {
    sortDirection = sortDirection === "asc" ? "desc" : "asc";
  } else {
    sortColumn = column;
    sortDirection = "asc";
  }

  // Only reset if sort actually changed
  if (prevSortColumn !== sortColumn || prevSortDirection !== sortDirection) {
    // Reset all state
    currentPage = 1;
    allDataLoaded = false;
    isLoading = false;

    // Clear existing data
    document.getElementById("tableBody").innerHTML = "";

    // Reset scroll position
    const scrollContainer = document.getElementById("scrollContainer");
    if (scrollContainer) {
      scrollContainer.scrollTop = 0;
    }

    // Remove existing sentinel and observer
    if (observer) {
      observer.disconnect();
    }
    if (sentinel && sentinel.parentNode) {
      sentinel.parentNode.removeChild(sentinel);
    }

    // Fetch new data and reinitialize scroll after data is loaded
    fetchTableData().then(() => {
      initializeInfiniteScroll();
    });
  }
}

function updateSortIndicators() {
  const headers = document.querySelectorAll("#tableHeader th");
  headers.forEach((header) => {
    const column = header.getAttribute("data-column");
    const indicator = header.querySelector(".sort-indicator");

    if (column === sortColumn) {
      indicator.innerHTML = sortDirection === "asc" ? "&uarr;" : "&darr;";
    } else {
      indicator.innerHTML = "";
    }
  });
}

function selectCell(cell) {
  if (previouslySelectedCell) {
    previouslySelectedCell.classList.remove("selected-cell");
  }
  cell.classList.add("selected-cell");
  previouslySelectedCell = cell;
}

function startEdit(cell) {
  currentlyEditingCell = cell;
  const currentValue = cell.textContent.trim();
  const column = cell.dataset.column;
  const type = cell.dataset.type;

  currentlyEditingCellData = {
    column: column,
    type: type,
    originalValue: currentValue,
  };

  let idValue = cell.dataset.idValue;
  currentlyEditingCellData.idValue = idValue;

  if (!idValue) {
    console.error("Could not find ID value");
    alert("Could not find ID value");
    return;
  }

  const modalInputContainer = document.getElementById("modalInputContainer");
  modalInputContainer.innerHTML = "";

  const input = createInputElement(type, currentValue);
  input.id = "modalInputField";
  modalInputContainer.appendChild(input);

  editModal.showModal();
}

function formatValueForInput(type, value) {
  if (!value) return "";
  if (type !== "date") return value;
  const date = new Date(value);
  return isNaN(date.getTime()) ? value : date.toISOString().split('T')[0];
}

function createInputElement(type, currentValue) {
  const input = document.createElement("input");
  input.type = type === "date" ? "date" : type === "int" ? "number" : "text";
  input.value = formatValueForInput(type, currentValue);
  input.classList.add("w-full", "p-2", "border", "rounded-sm", "allow-select");
  return input;
}

function parseValueFromInput(type, value) {
  // Number(), not parseInt()/parseFloat(): "1.5" and "52,41" must not save as 1 and 52.
  switch (type) {
    case "int":
      const intValue = Number(value.trim());
      if (value.trim() === "" || !Number.isInteger(intValue))
        throw new Error("Please enter a valid integer.");
      return intValue;
    case "float":
      const floatValue = Number(value.trim().replace(",", "."));
      if (value.trim() === "" || !Number.isFinite(floatValue))
        throw new Error("Please enter a valid number.");
      return floatValue;
    default:
      return value;
  }
}

function updateCell(column, newValue, cell) {
  const idValue = currentlyEditingCellData.idValue;
  const type = currentlyEditingCellData.type;

  if (!idValue) {
    console.error("Could not find ID value");
    alert("Could not find ID value");
    return;
  }

  let formattedValue;
  try {
    formattedValue = parseValueFromInput(type, newValue);
  } catch (e) {
    alert(e.message);
    return;
  }

  showLoadingIndicator();

  fetch("/admin/update_cell", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content,
    },
    body: JSON.stringify({
      column: column,
      meldungen_id: idValue,
      value: formattedValue,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        cell.textContent = newValue;
        currentlyEditingCell = null;
        currentlyEditingCellData = null;
      } else {
        alert("Failed to update: " + (data.error || "Unknown error"));
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert(
        "An error occurred while updating the cell. Please try again later."
      );
    })
    .finally(() => {
      hideLoadingIndicator();
    });
}

function saveState() {
  localStorage.setItem("searchTerm", searchTerm);
  localStorage.setItem("sortColumn", sortColumn);
  localStorage.setItem("sortDirection", sortDirection);
  localStorage.setItem("searchType", document.getElementById("searchType").value);
}

function loadState() {
  searchTerm = localStorage.getItem("searchTerm") || "";
  sortColumn = localStorage.getItem("sortColumn") || "meldungen_id";
  sortDirection = localStorage.getItem("sortDirection") || "asc";
  const savedSearchType = localStorage.getItem("searchType");

  currentPage = 1;  // Always start from page 1

  if (savedSearchType) {
    document.getElementById("searchType").value = savedSearchType;
  }

  document.getElementById("searchInput").value = searchTerm;
  changeInputPattern();
  return fetchTableData();
}

function clearSearch() {
  document.getElementById("searchInput").value = "";
  applySearch("");
}

// Restart the table from page 1 with a new search term.
function applySearch(term) {
  searchTerm = term;
  currentPage = 1;
  allDataLoaded = false;
  document.getElementById("tableBody").innerHTML = "";
  initializeInfiniteScroll();
  fetchTableData();
  saveState();
}

function changeInputPattern() {
  const searchType = document.getElementById('searchType').value;
  const searchInput = document.getElementById('searchInput');

  if (searchType === 'id') {
    searchInput.setAttribute('pattern', '\\d+');
    searchInput.setAttribute('title', 'Only IDs are allowed');
    searchInput.setAttribute('inputmode', 'numeric');
  } else {
    searchInput.removeAttribute('pattern');
    searchInput.removeAttribute('title');
    searchInput.setAttribute('inputmode', 'text');
  }
}
