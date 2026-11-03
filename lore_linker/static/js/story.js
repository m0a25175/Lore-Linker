const storyUrlInput = document.getElementById("story-url");
const fetchStoryButton = document.getElementById("fetch-story-button");
const storyFetchStatus = document.getElementById("story-fetch-status");

const storyPreview = document.getElementById("story-preview");
const previewStoryTitle = document.getElementById("preview-story-title");
const previewChampionList = document.getElementById("preview-champion-list");
const previewChampionSelect = document.getElementById("preview-champion-select");
const previewStoryBody = document.getElementById("preview-story-body");

let fetchedBiographies = [];

function showFetchStatus(message, type = "") {
  storyFetchStatus.textContent = message;
  storyFetchStatus.className = "story-fetch-status";

  if (type) {
    storyFetchStatus.classList.add(type);
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

previewChampionSelect.addEventListener(
    "change",
    displaySelectedBiography
);