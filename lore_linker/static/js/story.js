const storyUrlInput = document.getElementById("story-url");
const championSelect = document.getElementById("champion-select");
const registeredStoriesStatus = document.getElementById(
    "registered-stories-status"
);
const registeredStoriesList = document.getElementById(
    "registered-stories-list"
);
const storyEditFormContainer = document.getElementById(
    "story-edit-form-container"
);

const editStoryId = document.getElementById("edit-story-id");
const editStoryTitle = document.getElementById("edit-story-title");
const editStoryBody = document.getElementById("edit-story-body");
const editStoryChampion = document.getElementById("edit-story-champion");
const editStorySourceUrl = document.getElementById("edit-story-source-url");
const editStoryRegistrationMethod = document.getElementById("edit-story-registration-method");

const saveStoryEditButton = document.getElementById(
    "save-story-edit-button"
);

const cancelStoryEditButton = document.getElementById(
    "cancel-story-edit-button"
);

const storyEditStatus = document.getElementById("story-edit-status");
const fetchStoryButton = document.getElementById("fetch-story-button");
const storyFetchStatus = document.getElementById("story-fetch-status");
const registerStoryButton = document.getElementById("register-story-button");
const registerDuplicateStoryButton = document.getElementById("register-duplicate-story-button");
const storyRegistrationStatus = document.getElementById("story-registration-status");

const storyPreview = document.getElementById("story-preview");
const previewStoryTitle = document.getElementById("preview-story-title");
const previewChampionList = document.getElementById("preview-champion-list");
const previewChampionSelect = document.getElementById("preview-champion-select");
const previewStoryBody = document.getElementById("preview-story-body");
const duplicateStoryInfo = document.getElementById("duplicate-story-info");

const manualStoryChampionSelect = document.getElementById("manual-story-champion");
const manualStoryTitleInput = document.getElementById("manual-story-title");
const manualStoryBodyInput = document.getElementById("manual-story-body");
const registerManualStoryButton = document.getElementById("register-manual-story-button");
const registerManualDuplicateStoryButton = document.getElementById("register-manual-duplicate-story-button");
const manualDuplicateStoryInfo = document.getElementById("manual-duplicate-story-info");
const manualStoryRegistrationStatus = document.getElementById("manual-story-registration-status");

let fetchedBiographies = [];
let fetchedStoryData = null;
let duplicateStories = [];
let manualDuplicateStories = [];

function showFetchStatus(message, type = "") {
    storyFetchStatus.textContent = message;
    storyFetchStatus.className = "story-fetch-status";

    if (type) {
    storyFetchStatus.classList.add(type);
    }
}

function showManualStoryRegistrationStatus(message, type = "") {
    manualStoryRegistrationStatus.textContent = message;
    manualStoryRegistrationStatus.className = "story-fetch-status";

    if (type) {
        manualStoryRegistrationStatus.classList.add(type);
    }
}

function showRegisteredStoriesStatus(message, type = "") {
    registeredStoriesStatus.textContent = message;
    registeredStoriesStatus.className = "story-fetch-status";

    if (type) {
        registeredStoriesStatus.classList.add(type);
    }
}

function showStoryEditStatus(message, type = "") {
    storyEditStatus.textContent = message;
    storyEditStatus.className = "story-fetch-status";

    if (type) {
        storyEditStatus.classList.add(type);
    }
}

function displayRegisteredStories(stories) {
    registeredStoriesList.replaceChildren();

    if (stories.length === 0) {
        const emptyMessage = document.createElement("p");
        emptyMessage.textContent = "No stories registered for this champion.";
        registeredStoriesList.appendChild(emptyMessage);
        return;
    }

    stories.forEach((story) => {
        const storyItem = document.createElement("div");
        storyItem.className = "registered-story-item";

        const title = document.createElement("h4");
        title.textContent = story.title;

        const champion = document.createElement("p");
        champion.textContent = story.champion_id;

        const language = document.createElement("p");
        language.textContent =
            story.language_status === "accepted"
                ? "Language: English (accepted)"
                : `Language: Excluded (${story.language_reason || "No reason provided"})`;

        const method = document.createElement("p");
        method.textContent =
            `Registration method: ${story.registration_method}`;

                const actions = document.createElement("div");
        actions.className = "story-actions";

        const editButton = document.createElement("button");
        editButton.type = "button";
        editButton.className = "button-secondary";
        editButton.textContent = "Edit";
        editButton.dataset.storyId = story.id;

        const deleteButton = document.createElement("button");
        deleteButton.type = "button";
        deleteButton.className = "button-danger";
        deleteButton.textContent = "Delete";
        deleteButton.dataset.storyId = story.id;

        actions.append(
            editButton,
            deleteButton
        );

        storyItem.append(
            title,
            champion,
            language,
            method,
            actions
        );

        registeredStoriesList.appendChild(storyItem);
    });
}

async function loadRegisteredStories() {
    const championId = championSelect.value;

    registeredStoriesList.replaceChildren();

    showRegisteredStoriesStatus(
        "Loading registered stories...",
        "loading"
    );

    try {
        const query = championId
            ? `?champion=${encodeURIComponent(championId)}`
            : "";

        const response = await fetch(
            `/api/stories${query}`
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.error || "Failed to load registered stories."
            );
        }

        displayRegisteredStories(data.stories);

        showRegisteredStoriesStatus(
            `${data.stories.length} stories found.`,
            "success"
        );

    } catch (error) {
        showRegisteredStoriesStatus(
            error.message,
            "error"
        );
    }
}

async function deleteStory(storyId) {
    const confirmed = window.confirm(
        "Are you sure you want to delete this story?"
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(
            `/api/stories/${storyId}`,
            {
                method: "DELETE",
            }
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.error || "Failed to delete story."
            );
        }

        showRegisteredStoriesStatus(
            "Story deleted successfully.",
            "success"
        );

        await loadRegisteredStories();

    } catch (error) {
        showRegisteredStoriesStatus(
            error.message,
            "error"
        );
    }
}

async function openStoryEditForm(storyId) {
    showRegisteredStoriesStatus(
        "Loading story details...",
        "loading"
    );

    try {
        const response = await fetch(
            `/api/stories/${storyId}`
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.error || "Failed to load story details."
            );
        }

        const story = data.story;

        editStoryId.value = story.id;
        editStoryTitle.value = story.title;
        editStoryBody.value = story.body;
        editStoryChampion.value = story.champion_id;
        editStorySourceUrl.value = story.source_url || "";
        editStoryRegistrationMethod.value = story.registration_method;

        storyEditFormContainer.hidden = false;

        showRegisteredStoriesStatus("", "");

        storyEditFormContainer.scrollIntoView({
            behavior: "smooth",
            block: "start",
        });

    } catch (error) {
        showRegisteredStoriesStatus(
            error.message,
            "error"
        );
    }
}

async function saveStoryEdit() {
    const storyId = editStoryId.value;

    const title = editStoryTitle.value.trim();
    const body = editStoryBody.value.trim();

    if (!title || !body) {
        showStoryEditStatus(
            "Title and body are required.",
            "error"
        );
        return;
    }

    saveStoryEditButton.disabled = true;

    showStoryEditStatus(
        "Saving changes...",
        "loading"
    );

    try {
        const response = await fetch(
            `/api/stories/${storyId}`,
            {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    champion_name: editStoryChampion.value,
                    title,
                    body,
                    source_url: editStorySourceUrl.value || null,
                    registration_method: editStoryRegistrationMethod.value,
                    allow_duplicate: false,
                }),
            }
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.error || "Failed to update story."
            );
        }

        showStoryEditStatus(
            "Story updated successfully.",
            "success"
        );

        storyEditFormContainer.hidden = true;

        await loadRegisteredStories();

    } catch (error) {
        showStoryEditStatus(
            error.message,
            "error"
        );

    } finally {
        saveStoryEditButton.disabled = false;
    }
}

function displaySelectedBiography() {
    const selectedIndex = Number(previewChampionSelect.value);
    const selectedBiography = fetchedBiographies[selectedIndex];

    if (!selectedBiography) {
        previewStoryBody.textContent = "";
        return;
    }

    previewStoryBody.textContent = selectedBiography.body;
}

function populateChampionSelect(biographies) {
    previewChampionSelect.replaceChildren();

    biographies.forEach((biography, index) => {
        const option = document.createElement("option");

        option.value = String(index);
        option.textContent = biography.champion_name;

        previewChampionSelect.appendChild(option);
    });

    previewChampionList.textContent = biographies
        .map((biography) => biography.champion_name)
        .join(", ");
}

function displayStoryPreview(data) {
    fetchedBiographies = data.biographies;

    previewStoryTitle.textContent = data.title;

    populateChampionSelect(fetchedBiographies);

    displaySelectedBiography();

    storyPreview.hidden = false;
}

async function registerStory(allowDuplicate = false) {
    if (!fetchedStoryData || !fetchedBiographies.length) {
        storyRegistrationStatus.textContent =
            "Please fetch a story before registering.";
        return;
    }

    const selectedIndex = Number(previewChampionSelect.value);
    const selectedBiography = fetchedBiographies[selectedIndex];

    if (!selectedBiography) {
        storyRegistrationStatus.textContent =
            "Please select a champion.";
        return;
    }

    registerStoryButton.disabled = true;
    storyRegistrationStatus.textContent = "Registering story...";

    try {
        const response = await fetch("/api/stories", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                champion_name: selectedBiography.champion_name,
                title: fetchedStoryData.title,
                body: selectedBiography.body,
                source_url: storyUrlInput.value.trim(),
                registration_method: "url",
                allow_duplicate: allowDuplicate,
            }),
        });

        const data = await response.json();
        console.log("Story registration response:", response.status, data);

        if (response.status === 409 && data.duplicate) {
            duplicateStories = data.existing_stories || [];

            duplicateStoryInfo.textContent = duplicateStories
                .map((story) => {
                    return `${story.title} (${story.champion_id})`;
                })
                .join(", ");

            duplicateStoryInfo.hidden = false;
            registerDuplicateStoryButton.hidden = false;

            storyRegistrationStatus.textContent =
                "Duplicate story detected. Register anyway?";

            return;
        }

        if (!response.ok || !data.success) {
            throw new Error(
                data.error || "Failed to register story."
            );
        }

        duplicateStories = [];
        duplicateStoryInfo.textContent = "";
        duplicateStoryInfo.hidden = true;
        registerDuplicateStoryButton.hidden = true;
        storyRegistrationStatus.textContent =
            "Story registered successfully.";

        await loadRegisteredStories();

    } catch (error) {
        storyRegistrationStatus.textContent = error.message;

    } finally {
        registerStoryButton.disabled = false;
    }
}

async function registerManualStory(allowDuplicate = false) {
    const championName = manualStoryChampionSelect.value;
    const title = manualStoryTitleInput.value.trim();
    const body = manualStoryBodyInput.value.trim();

    if (!championName || !title || !body) {
        showManualStoryRegistrationStatus(
            "Please select a champion and enter both the title and story body.",
            "error"
        );
        return;
    }

    registerManualStoryButton.disabled = true;
    registerManualDuplicateStoryButton.disabled = true;

    showManualStoryRegistrationStatus(
        "Registering story...",
        "loading"
    );

    try {
        const response = await fetch("/api/stories", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                champion_name: championName,
                title: title,
                body: body,
                source_url: null,
                registration_method: "manual",
                allow_duplicate: allowDuplicate,
            }),
        });

        const data = await response.json();

        if (response.status === 409 && data.duplicate) {
            manualDuplicateStories = data.existing_stories || [];

            manualDuplicateStoryInfo.textContent = manualDuplicateStories
                .map((story) => {
                    return `${story.title} (${story.champion_id})`;
                })
                .join(", ");

            manualDuplicateStoryInfo.hidden = false;
            registerManualDuplicateStoryButton.hidden = false;

            showManualStoryRegistrationStatus(
                "Duplicate story detected. Register anyway?",
                "error"
            );

            return;
        }

    if (!response.ok || !data.success) {
        throw new Error(
            data.error || "Failed to register story."
        );
    }

    manualDuplicateStories = [];
    manualDuplicateStoryInfo.textContent = "";
    manualDuplicateStoryInfo.hidden = true;
    registerManualDuplicateStoryButton.hidden = true;

    showManualStoryRegistrationStatus(
        "Story registered successfully.",
        "success"
    );

    manualStoryTitleInput.value = "";
    manualStoryBodyInput.value = "";

    await loadRegisteredStories();

    } catch (error) {
        showManualStoryRegistrationStatus(error.message, "error");

    } finally {
        registerManualStoryButton.disabled = false;
        registerManualDuplicateStoryButton.disabled = false;
    }
}

async function fetchStory() {
    const url = storyUrlInput.value.trim();

    if (!url) {
        showFetchStatus("Please enter a Riot Universe URL.", "error");
        return;
    }

    fetchStoryButton.disabled = true;
    showFetchStatus("Loading story...", "loading");
    storyPreview.hidden = true;

    try {
        const response = await fetch("/api/stories/preview", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ url }),
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.error || "Failed to retrieve story."
            );
        }

        fetchedStoryData = data;
        displayStoryPreview(data);

        showFetchStatus(
            "Story retrieved successfully.",
            "success"
        );

    } catch (error) {
        showFetchStatus(error.message, "error");

    } finally {
        fetchStoryButton.disabled = false;
    }
}

fetchStoryButton.addEventListener("click", fetchStory);
registerStoryButton.addEventListener(
    "click",
    () => registerStory(false)
);

previewChampionSelect.addEventListener(
    "change",
    displaySelectedBiography
);

championSelect.addEventListener(
    "change",
    loadRegisteredStories
);

loadRegisteredStories();

registeredStoriesList.addEventListener("click", (event) => {
    const editButton = event.target.closest(
        ".button-secondary"
    );

    const deleteButton = event.target.closest(
        ".button-danger"
    );

    if (editButton && registeredStoriesList.contains(editButton)) {
        const storyId = editButton.dataset.storyId;

        if (storyId) {
            openStoryEditForm(storyId);
        }

        return;
    }

    if (deleteButton && registeredStoriesList.contains(deleteButton)) {
        const storyId = deleteButton.dataset.storyId;

        if (storyId) {
            deleteStory(storyId);
        }
    }
});

saveStoryEditButton.addEventListener("click", saveStoryEdit);

cancelStoryEditButton.addEventListener("click", () => {
    storyEditFormContainer.hidden = true;
    storyEditStatus.textContent = "";
});

registerDuplicateStoryButton.addEventListener(
    "click",
    () => registerStory(true)
);

registerManualStoryButton.addEventListener(
    "click",
    () => registerManualStory(false)
);

registerManualDuplicateStoryButton.addEventListener(
    "click",
    () => registerManualStory(true)
);
