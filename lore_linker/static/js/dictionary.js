const dictionaryTermsList = document.getElementById(
    "dictionary-terms-list"
);

const dictionarySearch = document.getElementById(
    "dictionary-search"
);

const dictionaryAddForm = document.getElementById(
    "dictionary-add-form"
);

const newTermInput = document.getElementById("new-term");

const dictionaryAddStatus = document.getElementById(
    "dictionary-add-status"
);

const dictionaryListStatus = document.getElementById(
    "dictionary-list-status"
);

const dictionaryEditContainer = document.getElementById(
    "dictionary-edit-container"
);

const dictionaryEditForm = document.getElementById(
    "dictionary-edit-form"
);

const editTermId = document.getElementById("edit-term-id");
const editTermInput = document.getElementById("edit-term");

const dictionaryEditStatus = document.getElementById(
    "dictionary-edit-status"
);

const cancelEditTermButton = document.getElementById(
    "cancel-edit-term"
);

const dictionaryResultCount = document.getElementById(
    "dictionary-result-count"
);

let dictionaryTerms = [];


/* ==============================
   Status Messages
============================== */

function showDictionaryStatus(element, message, type = "") {
    element.textContent = message;
    element.className = "dictionary-status";

    if (type) {
        element.classList.add(type);
    }
}


/* ==============================
   API Requests
============================== */

async function dictionaryRequest(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
    });

    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error("The server returned an invalid response.");
    }

    if (!response.ok || !data.success) {
        throw new Error(
            data.error || data.message || "An unexpected error occurred."
        );
    }

    return data;
}


/* ==============================
   Load Dictionary
============================== */

async function loadDictionaryTerms() {
    showDictionaryStatus(
        dictionaryListStatus,
        "Loading dictionary terms...",
        "loading"
    );

    try {
        const data = await dictionaryRequest(
            "/api/dictionary/terms"
        );

        dictionaryTerms = data.terms || [];

        renderDictionaryTerms();

        showDictionaryStatus(dictionaryListStatus, "");

    } catch (error) {
        showDictionaryStatus(
            dictionaryListStatus,
            error.message,
            "error"
        );
    }
}


/* ==============================
   Dictionary Overview
============================== */

async function loadDictionaryOverview() {
    try {
        const data = await dictionaryRequest(
            "/api/dictionary/overview"
        );

        const overview = data.overview;

        document.getElementById("total-terms").textContent =
            overview.total_terms;

        document.getElementById("used-terms").textContent =
            overview.used_terms;

        document.getElementById("unused-terms").textContent =
            overview.unused_terms;

    } catch (error) {
        console.error("Failed to load dictionary overview:", error);
    }
}


/* ==============================
   Render Dictionary Terms
============================== */

function renderDictionaryTerms() {
    const keyword = dictionarySearch.value.trim().toLowerCase();

    const filteredTerms = dictionaryTerms.filter((item) =>
        item.term.toLowerCase().includes(keyword)
    );

    dictionaryTermsList.replaceChildren();

    if (filteredTerms.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = 4;
        cell.className = "dictionary-empty";

        cell.textContent = dictionaryTerms.length === 0
            ? "No terms registered yet."
            : "No matching terms found.";

        row.appendChild(cell);
        dictionaryTermsList.appendChild(row);

        dictionaryResultCount.textContent = "0 terms";
        return;
    }

    filteredTerms.forEach((item) => {
        const row = document.createElement("tr");

        const termCell = document.createElement("td");
        termCell.className = "dictionary-term-name";
        termCell.textContent = item.term;

        const usageCell = document.createElement("td");
        const usageBadge = document.createElement("span");

        usageBadge.className = Number(item.usage_count) > 0
            ? "dictionary-usage-badge used"
            : "dictionary-usage-badge unused";

        usageBadge.textContent = item.usage_count;
        usageCell.appendChild(usageBadge);

        const dateCell = document.createElement("td");
        dateCell.textContent = item.created_at || "-";

        const actionsCell = document.createElement("td");
        const actions = document.createElement("div");

        actions.className = "dictionary-actions";

        const editButton = document.createElement("button");

        editButton.type = "button";
        editButton.className = "button-secondary";
        editButton.textContent = "Edit";

        editButton.addEventListener("click", () => {
            openEditForm(item);
        });

        const deleteButton = document.createElement("button");

        deleteButton.type = "button";
        deleteButton.className = "button-danger";
        deleteButton.textContent = "Delete";

        deleteButton.addEventListener("click", () => {
            deleteDictionaryTerm(item);
        });

        actions.append(editButton, deleteButton);
        actionsCell.appendChild(actions);

        row.append(
            termCell,
            usageCell,
            dateCell,
            actionsCell
        );

        dictionaryTermsList.appendChild(row);
    });

    dictionaryResultCount.textContent =
        `${filteredTerms.length} of ${dictionaryTerms.length} terms`;
}


/* ==============================
   Add Dictionary Term
============================== */

dictionaryAddForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const term = newTermInput.value.trim();

    if (!term) {
        showDictionaryStatus(
            dictionaryAddStatus,
            "Please enter a term.",
            "error"
        );
        return;
    }

    try {
        await dictionaryRequest(
            "/api/dictionary/terms",
            {
                method: "POST",
                body: JSON.stringify({ term }),
            }
        );

        newTermInput.value = "";

        showDictionaryStatus(
            dictionaryAddStatus,
            "Term registered successfully.",
            "success"
        );

        await refreshDictionary();

    } catch (error) {
        showDictionaryStatus(
            dictionaryAddStatus,
            error.message,
            "error"
        );
    }
});


/* ==============================
   Edit Dictionary Term
============================== */

function openEditForm(item) {
    editTermId.value = item.id;
    editTermInput.value = item.term;

    showDictionaryStatus(dictionaryEditStatus, "");

    dictionaryEditContainer.hidden = false;

    dictionaryEditContainer.scrollIntoView({
        behavior: "smooth",
        block: "center",
    });

    editTermInput.focus();
}


function closeEditForm() {
    dictionaryEditContainer.hidden = true;
    dictionaryEditForm.reset();

    showDictionaryStatus(dictionaryEditStatus, "");
}


dictionaryEditForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const id = editTermId.value;
    const term = editTermInput.value.trim();

    if (!term) {
        showDictionaryStatus(
            dictionaryEditStatus,
            "Please enter a term.",
            "error"
        );
        return;
    }

    try {
        await dictionaryRequest(
            `/api/dictionary/terms/${id}`,
            {
                method: "PUT",
                body: JSON.stringify({ term }),
            }
        );

        closeEditForm();

        await refreshDictionary();

    } catch (error) {
        showDictionaryStatus(
            dictionaryEditStatus,
            error.message,
            "error"
        );
    }
});


cancelEditTermButton.addEventListener("click", closeEditForm);


/* ==============================
   Delete Dictionary Term
============================== */

async function deleteDictionaryTerm(item) {
    const usageCount = Number(item.usage_count) || 0;

    let message =
        `Delete the dictionary term "${item.term}"?`;

    if (usageCount > 0) {
        message +=
            `\n\nThis term is currently used by ${usageCount} registered story record(s).`;

        message +=
            "\n\nDeleting it will also delete its associated story_terms records.";

        message +=
            "\nThis operation cannot be undone.";
    } else {
        message +=
            "\n\nThis operation cannot be undone.";
    }

    if (!window.confirm(message)) {
        return;
    }

    try {
        const data = await dictionaryRequest(
            `/api/dictionary/terms/${item.id}`,
            {
                method: "DELETE",
            }
        );

        showDictionaryStatus(
            dictionaryListStatus,
            `"${data.deleted_term}" was deleted successfully.`,
            "success"
        );

        await refreshDictionary();

    } catch (error) {
        showDictionaryStatus(
            dictionaryListStatus,
            error.message,
            "error"
        );
    }
}


/* ==============================
   Search
============================== */

dictionarySearch.addEventListener("input", () => {
    renderDictionaryTerms();
});


/* ==============================
   Refresh
============================== */

async function refreshDictionary() {
    await Promise.all([
        loadDictionaryTerms(),
        loadDictionaryOverview(),
    ]);
}


/* ==============================
   Initialization
============================== */

document.addEventListener("DOMContentLoaded", () => {
    refreshDictionary();
});

/* ==============================
   Dictionary Candidate Collection
============================== */

const collectCandidatesButton = document.getElementById(
    "collect-dictionary-candidates"
);

const candidateStatus = document.getElementById(
    "dictionary-candidate-status"
);

const candidateContainer = document.getElementById(
    "dictionary-candidate-container"
);

const candidateCount = document.getElementById(
    "dictionary-candidate-count"
);

const candidateSearch = document.getElementById(
    "dictionary-candidate-search"
);

const candidatesList = document.getElementById(
    "dictionary-candidates-list"
);

const selectAllCandidatesButton = document.getElementById(
    "select-all-candidates"
);

const clearAllCandidatesButton = document.getElementById(
    "clear-all-candidates"
);

const registerCandidatesButton = document.getElementById(
    "register-selected-candidates"
);

let dictionaryCandidates = [];
let selectedCandidateTerms = new Set();


function updateCandidateSelection() {
    const visibleTerms = getFilteredCandidates();

    const visibleSelectedCount = visibleTerms.filter(
        (item) => selectedCandidateTerms.has(item.term)
    ).length;

    registerCandidatesButton.disabled =
        selectedCandidateTerms.size === 0;

    registerCandidatesButton.textContent =
        `Register Selected Terms (${selectedCandidateTerms.size})`;

    selectAllCandidatesButton.disabled =
        visibleTerms.length === 0 ||
        visibleSelectedCount === visibleTerms.length;

    clearAllCandidatesButton.disabled =
        visibleSelectedCount === 0;
}


function getFilteredCandidates() {
    const keyword = candidateSearch.value.trim().toLowerCase();

    return dictionaryCandidates.filter((item) =>
        item.term.toLowerCase().includes(keyword)
    );
}


function renderDictionaryCandidates() {
    const filteredCandidates = getFilteredCandidates();

    candidatesList.replaceChildren();

    if (filteredCandidates.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = 4;
        cell.className = "dictionary-empty";
        cell.textContent = "No matching candidates found.";

        row.appendChild(cell);
        candidatesList.appendChild(row);

        updateCandidateSelection();

        return;
    }

    filteredCandidates.forEach((item) => {
        const row = document.createElement("tr");

        const selectCell = document.createElement("td");
        const checkbox = document.createElement("input");

        checkbox.type = "checkbox";
        checkbox.checked = selectedCandidateTerms.has(item.term);
        checkbox.setAttribute(
            "aria-label",
            `Select ${item.term}`
        );

        checkbox.addEventListener("change", () => {
            if (checkbox.checked) {
                selectedCandidateTerms.add(item.term);
            } else {
                selectedCandidateTerms.delete(item.term);
            }

            updateCandidateSelection();
        });

        selectCell.appendChild(checkbox);

        const termCell = document.createElement("td");
        termCell.className = "dictionary-term-name";
        termCell.textContent = item.term;

        const occurrenceCell = document.createElement("td");
        occurrenceCell.textContent = item.occurrence_count;

        const sourceCell = document.createElement("td");
        sourceCell.textContent = item.source_types.join(", ");

        row.append(
            selectCell,
            termCell,
            occurrenceCell,
            sourceCell
        );

        candidatesList.appendChild(row);
    });

    updateCandidateSelection();
}


async function collectDictionaryCandidates() {
    collectCandidatesButton.disabled = true;
    collectCandidatesButton.textContent = "Collecting...";

    showDictionaryStatus(
        candidateStatus,
        "Extracting candidate terms. Please wait...",
        "loading"
    );

    try {
        const data = await dictionaryRequest(
            "/api/dictionary/candidates"
        );

        dictionaryCandidates = data.candidates || [];
        selectedCandidateTerms.clear();

        candidateSearch.value = "";

        candidateContainer.hidden = false;

        candidateCount.textContent =
            `${data.total_candidates} candidates found`;

        renderDictionaryCandidates();

        showDictionaryStatus(
            candidateStatus,
            `${data.total_candidates} candidates collected. No terms have been registered yet.`,
            "success"
        );

    } catch (error) {
        showDictionaryStatus(
            candidateStatus,
            error.message,
            "error"
        );

    } finally {
        collectCandidatesButton.disabled = false;
        collectCandidatesButton.textContent = "Collect Candidates";
    }
}


collectCandidatesButton.addEventListener(
    "click",
    collectDictionaryCandidates
);


candidateSearch.addEventListener("input", () => {
    renderDictionaryCandidates();
});


selectAllCandidatesButton.addEventListener("click", () => {
    getFilteredCandidates().forEach((item) => {
        selectedCandidateTerms.add(item.term);
    });

    renderDictionaryCandidates();
});


clearAllCandidatesButton.addEventListener("click", () => {
    getFilteredCandidates().forEach((item) => {
        selectedCandidateTerms.delete(item.term);
    });

    renderDictionaryCandidates();
});


registerCandidatesButton.addEventListener(
    "click",
    async () => {
        const terms = Array.from(selectedCandidateTerms);

        if (terms.length === 0) {
            return;
        }

        const confirmed = window.confirm(
            `Register ${terms.length} selected dictionary terms?`
        );

        if (!confirmed) {
            return;
        }

        registerCandidatesButton.disabled = true;

        showDictionaryStatus(
            candidateStatus,
            "Registering selected terms...",
            "loading"
        );

        try {
            const data = await dictionaryRequest(
                "/api/dictionary/candidates/register",
                {
                    method: "POST",
                    body: JSON.stringify({ terms }),
                }
            );

            showDictionaryStatus(
                candidateStatus,
                `Registration completed. Added: ${data.inserted_count}, skipped: ${data.skipped_count}.`,
                "success"
            );

            // 登録された候補を一覧から除去
            const registeredTerms = new Set(terms);

            dictionaryCandidates = dictionaryCandidates.filter(
                (item) => !registeredTerms.has(item.term)
            );

            selectedCandidateTerms.clear();

            candidateCount.textContent =
                `${dictionaryCandidates.length} candidates remaining`;

            renderDictionaryCandidates();

            await refreshDictionary();

        } catch (error) {
            showDictionaryStatus(
                candidateStatus,
                error.message,
                "error"
            );

        } finally {
            updateCandidateSelection();
        }
    }
);
