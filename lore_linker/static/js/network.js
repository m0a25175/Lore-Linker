document.addEventListener("DOMContentLoaded", () => {
    const checkboxes = Array.from(
        document.querySelectorAll(".champion-checkbox")
    );

    const searchInput = document.getElementById("champion-search");
    const selectedCount = document.getElementById(
        "network-selected-count"
    );

    const thresholdInput = document.getElementById(
        "analysis-threshold"
    );

    const runButton = document.getElementById("run-analysis");
    const exportButton = document.getElementById("export-analysis");
    const pngButton = document.getElementById("export-network-png");
    const importButton = document.getElementById("import-analysis");
    const fileInput = document.getElementById("analysis-file");

    const statusElement = document.getElementById("analysis-status");

    const emptyElement = document.getElementById("network-empty");
    const visualContainer = document.getElementById(
        "network-visual-container"
    );

    const svg = document.getElementById("network-svg");
    const edgesBody = document.getElementById("network-edges-body");

    const nodeCountElement = document.getElementById(
        "network-node-count"
    );
    const edgeCountElement = document.getElementById(
        "network-edge-count"
    );
    const resultThresholdElement = document.getElementById(
        "network-result-threshold"
    );

    const selectionInfo = document.getElementById(
        "network-selection-info"
    );

    const SVG_NS = "http://www.w3.org/2000/svg";

    let currentResult = null;
    let selectedChampionId = null;
    let busy = false;

    function setStatus(message, type = "") {
        statusElement.textContent = message;
        statusElement.className = "network-status";

        if (type) {
            statusElement.classList.add(`status-${type}`);
        }
    }

    function setBusy(value) {
        busy = value;

        runButton.disabled = value;
        exportButton.disabled = value;
        importButton.disabled = value;
        pngButton.disabled = value || !currentResult;

        runButton.textContent = value
            ? "Processing..."
            : "Run Analysis";
    }

    function getSelectedChampions() {
        return checkboxes
            .filter((checkbox) => checkbox.checked)
            .map((checkbox) => checkbox.value);
    }

    function updateSelectedCount() {
        const count = getSelectedChampions().length;
        selectedCount.textContent = `${count} selected`;
    }

    function setSelectedChampions(ids) {
        const selected = new Set(ids || []);

        checkboxes.forEach((checkbox) => {
            checkbox.checked = selected.has(checkbox.value);
        });

        updateSelectedCount();
    }

    function createSvgElement(tag, attributes = {}) {
        const element = document.createElementNS(SVG_NS, tag);

        Object.entries(attributes).forEach(([key, value]) => {
            element.setAttribute(key, String(value));
        });

        return element;
    }

    function showEmptyState(message) {
        currentResult = null;
        pngButton.disabled = true;

        emptyElement.hidden = false;
        emptyElement.textContent = message;
        visualContainer.hidden = true;

        svg.replaceChildren();

        edgesBody.replaceChildren();

        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = 6;
        cell.className = "network-table-empty";
        cell.textContent = "No relationships to display.";

        row.appendChild(cell);
        edgesBody.appendChild(row);

        nodeCountElement.textContent = "0";
        edgeCountElement.textContent = "0";
        resultThresholdElement.textContent = "-";
    }

    function renderNetwork(result) {
        if (!result || !Array.isArray(result.nodes)) {
            showEmptyState("No analysis result is available.");
            return;
        }

        currentResult = result;
        selectedChampionId = null;

        const nodes = result.nodes;
        const edges = Array.isArray(result.edges)
            ? result.edges
            : [];

        nodeCountElement.textContent = result.node_count ?? nodes.length;
        edgeCountElement.textContent = result.edge_count ?? edges.length;
        resultThresholdElement.textContent =
            `${Number(result.threshold ?? 0).toFixed(1)}%`;

        emptyElement.hidden = true;
        visualContainer.hidden = false;

        svg.replaceChildren();

        // ノード数に応じて同心円の数と描画領域を決定する
        const ringStartRadius = 160;
        const ringSpacing = 130;
        const minimumNodeSpacing = 125;
        const nodeRadius = 22;

        const rings = [];
        let remaining = nodes.length;
        let ringIndex = 0;

        while (remaining > 0) {
            const radius = ringStartRadius + ringIndex * ringSpacing;
            const capacity = Math.max(
                1,
                Math.floor(
                    (2 * Math.PI * radius) / minimumNodeSpacing
                )
            );

            const count = Math.min(remaining, capacity);

            rings.push({
                radius,
                count,
                startIndex: nodes.length - remaining
            });

            remaining -= count;
            ringIndex += 1;
        }

        const outerRadius = rings.length > 0
            ? rings[rings.length - 1].radius
            : 0;

        const padding = 110;
        const width = Math.max(
            1000,
            Math.ceil((outerRadius + padding) * 2)
        );
        const height = width;
        const centerX = width / 2;
        const centerY = height / 2;

        svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
        svg.setAttribute("width", String(width));
        svg.setAttribute("height", String(height));

        const positions = new Map();

        rings.forEach((ring) => {
            for (let i = 0; i < ring.count; i += 1) {
                const nodeIndex = ring.startIndex + i;
                const node = nodes[nodeIndex];

                const angle = ring.count === 1
                    ? -Math.PI / 2
                    : (2 * Math.PI * i / ring.count)
                        - Math.PI / 2;

                positions.set(node.champion_id, {
                    x: centerX + ring.radius * Math.cos(angle),
                    y: centerY + ring.radius * Math.sin(angle)
                });
            }
        });

        // 接続線
        const edgeGroup = createSvgElement("g", {
            class: "network-edges"
        });

        edges.forEach((edge) => {
            const source = positions.get(edge.source);
            const target = positions.get(edge.target);

            if (!source || !target) {
                return;
            }

            const line = createSvgElement("line", {
                x1: source.x,
                y1: source.y,
                x2: target.x,
                y2: target.y,
                class: "network-edge",
                "data-source": edge.source,
                "data-target": edge.target,
                "stroke-width": Math.max(
                    1,
                    Math.min(7, Number(edge.score || 0) / 12)
                )
            });

            const title = createSvgElement("title");
            title.textContent =
                `${edge.source} - ${edge.target}: ${edge.score}%`;

            line.appendChild(title);
            edgeGroup.appendChild(line);
        });

        svg.appendChild(edgeGroup);

        // チャンピオンノードとラベル
        const nodeGroup = createSvgElement("g", {
            class: "network-nodes"
        });

        nodes.forEach((node) => {
            const position = positions.get(node.champion_id);

            const group = createSvgElement("g", {
                class: "network-node",
                tabindex: "0",
                role: "button",
                "aria-label": `${node.name} relationships`
            });

            group.addEventListener("click", () => {
                const nextSelection =
                    selectedChampionId === node.champion_id
                        ? null
                        : node.champion_id;

                applyNodeSelection(nextSelection);
            });

            group.addEventListener("keydown", (event) => {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();

                    const nextSelection =
                        selectedChampionId === node.champion_id
                            ? null
                            : node.champion_id;

                    applyNodeSelection(nextSelection);
                }
            });

            const circle = createSvgElement("circle", {
                cx: position.x,
                cy: position.y,
                r: nodeRadius
            });

            const title = createSvgElement("title");
            title.textContent =
                `${node.name} | Stories: ${node.story_count} | Terms: ${node.term_count}`;

            circle.appendChild(title);

            const label = createSvgElement("text", {
                x: position.x,
                y: position.y + 40,
                "text-anchor": "middle",
                class: "network-node-label"
            });

            label.textContent = node.name;

            group.appendChild(circle);
            group.appendChild(label);
            nodeGroup.appendChild(group);
        });

        svg.appendChild(nodeGroup);

        renderEdgeTable(edges, nodes);
        applyNodeSelection(null);
    }

    function applyNodeSelection(championId) {
        selectedChampionId = championId;

        if (!currentResult) {
            return;
        }

        const nodes = currentResult.nodes || [];
        const edges = currentResult.edges || [];

        const connectedIds = new Set();

        if (championId) {
            connectedIds.add(championId);

            edges.forEach((edge) => {
                if (edge.source === championId) {
                    connectedIds.add(edge.target);
                } else if (edge.target === championId) {
                    connectedIds.add(edge.source);
                }
            });
        }

        svg.querySelectorAll(".network-node").forEach((group) => {
            const label = group.querySelector(".network-node-label");
            const node = nodes.find(
                (item) => item.name === label?.textContent
            );

            if (!node) {
                return;
            }

            group.classList.remove(
                "network-node-selected",
                "network-node-related",
                "network-node-dimmed"
            );

            if (!championId) {
                return;
            }

            if (node.champion_id === championId) {
                group.classList.add("network-node-selected");
            } else if (connectedIds.has(node.champion_id)) {
                group.classList.add("network-node-related");
            } else {
                group.classList.add("network-node-dimmed");
            }
        });

        svg.querySelectorAll(".network-edge").forEach((line) => {
            line.classList.remove(
                "network-edge-highlight",
                "network-edge-dimmed"
            );

            if (!championId) {
                return;
            }

            const connected =
                line.dataset.source === championId
                || line.dataset.target === championId;

            line.classList.add(
                connected
                    ? "network-edge-highlight"
                    : "network-edge-dimmed"
            );
        });

        const selectedNode = nodes.find(
            (node) => node.champion_id === championId
        );

        if (!championId) {
            selectionInfo.textContent =
                "Click a champion node to see its relationships and shared keywords.";
        } else {
            const connectionCount = edges.filter(
                (edge) =>
                    edge.source === championId
                    || edge.target === championId
            ).length;

            selectionInfo.textContent =
                `${selectedNode.name}: ${connectionCount} relationship(s). `
                + "The table below shows the connected champions and shared keywords. "
                + "Click the selected node again to clear the selection.";
        }

        renderEdgeTable(edges, nodes, championId);
    }

    function renderEdgeTable(edges, nodes, championId = null) {
        edgesBody.replaceChildren();

        const names = new Map(
            nodes.map((node) => [
                node.champion_id,
                node.name
            ])
        );

        const displayedEdges = championId
            ? edges.filter(
                (edge) =>
                    edge.source === championId
                    || edge.target === championId
            )
            : edges;

        if (displayedEdges.length === 0) {
            const row = document.createElement("tr");
            const cell = document.createElement("td");

            cell.colSpan = 6;
            cell.className = "network-table-empty";
            cell.textContent = championId
                ? "This champion has no relationships at the current threshold."
                : "No relationships meet the current threshold.";

            row.appendChild(cell);
            edgesBody.appendChild(row);
            return;
        }

        displayedEdges.forEach((edge) => {
            const row = document.createElement("tr");

            const values = [
                names.get(edge.source) || edge.source,
                names.get(edge.target) || edge.target,
                `${Number(edge.score).toFixed(2)}%`,
                `${Number(edge.common_word_score).toFixed(2)}%`,
                `${Number(edge.mutual_appearance_score).toFixed(2)}%`,
                Array.isArray(edge.shared_terms)
                    ? edge.shared_terms.join(", ")
                    : ""
            ];

            values.forEach((value) => {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
            });

            edgesBody.appendChild(row);
        });
    }

    async function loadLatestAnalysis() {
        try {
            const response = await fetch("/api/analysis/state");
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(
                    data.error || "Failed to load analysis state."
                );
            }

            if (!data.state) {
                showEmptyState("No saved analysis is available yet.");
                return;
            }

            setSelectedChampions(data.state.selected_champions || []);

            thresholdInput.value = data.state.threshold ?? 10;

            if (data.state.result) {
                renderNetwork(data.state.result);
                setStatus(
                    `Latest analysis restored. Updated at: ${data.state.updated_at}`,
                    "success"
                );
            } else {
                showEmptyState("Saved conditions found, but no result is available.");
            }
        } catch (error) {
            console.error(error);
            setStatus(error.message, "error");
        }
    }

    async function runAnalysis() {
        if (busy) {
            return;
        }

        const selectedChampions = getSelectedChampions();
        const threshold = Number(thresholdInput.value);

        if (selectedChampions.length === 0) {
            setStatus("Please select at least one champion.", "error");
            return;
        }

        if (
            !Number.isFinite(threshold)
            || threshold < 0
            || threshold > 100
        ) {
            setStatus("Threshold must be between 0 and 100.", "error");
            return;
        }

        setBusy(true);
        setStatus("Analysis is running...");

        try {
            const response = await fetch("/api/analysis/run", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    selected_champions: selectedChampions,
                    threshold: threshold
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(
                    data.error || "Analysis failed."
                );
            }

            renderNetwork(data);

            setStatus(
                `Analysis completed. ${data.node_count} champions and ${data.edge_count} relationships found.`,
                "success"
            );
        } catch (error) {
            console.error(error);
            setStatus(error.message, "error");
        } finally {
            setBusy(false);
        }
    }

    async function exportAnalysis() {
        if (busy) {
            return;
        }

        try {
            const response = await fetch("/api/analysis/export");
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(
                    data.error || "Export failed."
                );
            }

            const blob = new Blob(
                [JSON.stringify(data, null, 2)],
                { type: "application/json" }
            );

            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");

            link.href = url;
            link.download = "lore-linker-analysis.json";

            document.body.appendChild(link);
            link.click();
            link.remove();

            URL.revokeObjectURL(url);

            setStatus("Analysis JSON exported.", "success");
        } catch (error) {
            console.error(error);
            setStatus(error.message, "error");
        }
    }

    async function exportNetworkPng() {
        if (busy || !currentResult) {
            return;
        }

        try {
            const viewBox = svg.viewBox.baseVal;
            const width = Math.ceil(viewBox.width);
            const height = Math.ceil(viewBox.height);
            const scale = 2;

            // SVGを複製し、画面上のスタイルを画像にも反映する
            const clonedSvg = svg.cloneNode(true);

            clonedSvg.setAttribute("xmlns", SVG_NS);
            clonedSvg.setAttribute("width", String(width));
            clonedSvg.setAttribute("height", String(height));
            clonedSvg.setAttribute(
                "viewBox",
                `0 0 ${width} ${height}`
            );

            const originalElements = [
                svg,
                ...svg.querySelectorAll("*")
            ];
            const clonedElements = [
                clonedSvg,
                ...clonedSvg.querySelectorAll("*")
            ];

            const styleProperties = [
                "fill",
                "stroke",
                "stroke-width",
                "font-family",
                "font-size",
                "font-weight",
                "text-anchor",
                "opacity",
                "stroke-linecap",
                "stroke-dasharray"
            ];

            originalElements.forEach((element, index) => {
                const computed = getComputedStyle(element);
                const clone = clonedElements[index];

                styleProperties.forEach((property) => {
                    const value = computed.getPropertyValue(property);

                    if (value) {
                        clone.style.setProperty(property, value);
                    }
                });
            });

            // PNG用にチャンピオン名の視認性を確保する
            clonedSvg.querySelectorAll(".network-node-label")
                .forEach((label) => {
                    label.style.setProperty("fill", "#FFFFFF");
                    label.style.setProperty("font-family", "Arial, sans-serif");
                    label.style.setProperty("font-size", "20px");
                    label.style.setProperty("font-weight", "700");
                    label.style.setProperty("stroke", "#101827");
                    label.style.setProperty("stroke-width", "4px");
                    label.style.setProperty("stroke-linejoin", "round");
                    label.style.setProperty("paint-order", "stroke fill");
                    label.style.setProperty("text-anchor", "middle");
                });

            // 背景色を追加
            const backgroundColor =
                getComputedStyle(document.body)
                    .getPropertyValue("--background")
                    .trim() || "#101827";

            const background = createSvgElement("rect", {
                x: 0,
                y: 0,
                width,
                height,
                fill: backgroundColor
            });

            clonedSvg.insertBefore(
                background,
                clonedSvg.firstChild
            );

            const svgText = new XMLSerializer()
                .serializeToString(clonedSvg);

            const svgBlob = new Blob(
                [svgText],
                { type: "image/svg+xml;charset=utf-8" }
            );

            const svgUrl = URL.createObjectURL(svgBlob);

            try {
                const image = new Image();

                await new Promise((resolve, reject) => {
                    image.onload = resolve;
                    image.onerror = () => {
                        reject(new Error("Failed to render network image."));
                    };
                    image.src = svgUrl;
                });

                const canvas = document.createElement("canvas");
                canvas.width = width * scale;
                canvas.height = height * scale;

                const context = canvas.getContext("2d");

                if (!context) {
                    throw new Error("Canvas is not available.");
                }

                context.fillStyle = backgroundColor;
                context.fillRect(0, 0, canvas.width, canvas.height);
                context.drawImage(
                    image,
                    0,
                    0,
                    canvas.width,
                    canvas.height
                );

                const pngBlob = await new Promise((resolve, reject) => {
                    canvas.toBlob((blob) => {
                        if (blob) {
                            resolve(blob);
                        } else {
                            reject(new Error("Failed to create PNG."));
                        }
                    }, "image/png");
                });

                const pngUrl = URL.createObjectURL(pngBlob);
                const link = document.createElement("a");

                const timestamp = new Date()
                    .toISOString()
                    .replace(/[:.]/g, "-");

                link.href = pngUrl;
                link.download = `lore-linker-network_${timestamp}.png`;

                document.body.appendChild(link);
                link.click();
                link.remove();

                setTimeout(() => URL.revokeObjectURL(pngUrl), 1000);

                setStatus("Network PNG exported.", "success");
            } finally {
                URL.revokeObjectURL(svgUrl);
            }
        } catch (error) {
            console.error(error);
            setStatus(error.message, "error");
        }
    }

    async function importAnalysis(file) {
        if (!file || busy) {
            return;
        }

        setBusy(true);
        setStatus("Importing analysis...");

        try {
            const text = await file.text();
            const json = JSON.parse(text);

            const response = await fetch("/api/analysis/import", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(json)
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(
                    data.error || "Import failed."
                );
            }

            setSelectedChampions(
                data.result.selected_champions || []
            );

            thresholdInput.value = data.result.threshold ?? 10;

            renderNetwork(data.result);

            setStatus(
                "Analysis conditions imported and analysis completed.",
                "success"
            );
        } catch (error) {
            console.error(error);
            setStatus(error.message, "error");
        } finally {
            setBusy(false);
            fileInput.value = "";
        }
    }

    checkboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", updateSelectedCount);
    });

    document.getElementById("select-all-champions")
        .addEventListener("click", () => {
            checkboxes.forEach((checkbox) => {
                const option = checkbox.closest(".champion-option");

                if (!option.hidden) {
                    checkbox.checked = true;
                }
            });

            updateSelectedCount();
        });

    document.getElementById("clear-all-champions")
        .addEventListener("click", () => {
            checkboxes.forEach((checkbox) => {
                checkbox.checked = false;
            });

            updateSelectedCount();
        });

    searchInput.addEventListener("input", () => {
        const query = searchInput.value.trim().toLowerCase();

        document.querySelectorAll(".champion-option").forEach((option) => {
            option.hidden = !option.dataset.search
                .toLowerCase()
                .includes(query);
        });
    });

    runButton.addEventListener("click", runAnalysis);
    exportButton.addEventListener("click", exportAnalysis);
    pngButton.addEventListener("click", exportNetworkPng);

    importButton.addEventListener("click", () => {
        fileInput.click();
    });

    fileInput.addEventListener("change", () => {
        const file = fileInput.files[0];

        if (file) {
            importAnalysis(file);
        }
    });

    updateSelectedCount();
    loadLatestAnalysis();
});
