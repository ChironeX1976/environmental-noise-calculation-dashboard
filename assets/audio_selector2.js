function waitForTriggerElement() {
    const target = document.getElementById("js-trigger");
    if (target) {
        const observer = new MutationObserver(() => {
            const rawData = target.dataset.files;
            if (rawData) {
                try {
                    const parsed = JSON.parse(rawData);
                    console.log("📨 allowedFilesReady ontvangen:", parsed);
                    initAudioSelector(parsed);
                    observer.disconnect();
                } catch (e) {
                    console.error("❌ Fout bij JSON parse:", e);
                }
            }
        });

        observer.observe(target, {
            attributes: true,
            attributeFilter: ["data-files"]
        });
    } else {
        console.warn("⏳ Wachten op js-trigger element...");
        setTimeout(waitForTriggerElement, 500); // probeer opnieuw na 500ms
    }
}

waitForTriggerElement();
