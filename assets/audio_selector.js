function initAudioSelector(toegestaneBestanden) {
  // Haal de benodigde HTML-elementen op
  const selectFolderBtn = document.getElementById('select-folder'); // knop om map te selecteren
  const fileList = document.getElementById('file-list'); // dropdown om audiobestand te kiezen
  const audioPlayer = document.getElementById('audio-player'); // audio player element
  const errorMessage = document.getElementById('error-message'); // foutmelding element
  let audioFiles = []; // lijst om geldige audiobestanden op te slaan

  // Zet de toegestane bestanden om in een Map voor snelle lookup
  const toegestaneMap = new Map(
    toegestaneBestanden.map(item => [item.value, item.label])
  );

  // Voeg een click-event toe aan de knop om een map te selecteren
  selectFolderBtn.addEventListener('click', async () => {
    try {
      // Open de folder picker (vereist permissie van de gebruiker)
      const dirHandle = await window.showDirectoryPicker();

      // Reset de dropdown en foutmeldingen
      fileList.innerHTML = '<option disabled selected>Select an audio file</option>';
      fileList.disabled = true;
      audioFiles = [];
      errorMessage.textContent = '';

      // Loop door alle bestanden in de geselecteerde map
      for await (const entry of dirHandle.values()) {
        // Controleer of het een audiobestand is én of het in de toegestane lijst staat
        if (
          entry.kind === 'file' &&
          /\.(mp3|wav)$/i.test(entry.name) &&
          toegestaneMap.has(entry.name)
        ) {
          // Lees het bestand en maak een tijdelijke URL aan
          const file = await entry.getFile();
          const url = URL.createObjectURL(file);

          // Voeg het bestand toe aan de lijst
          audioFiles.push({ name: entry.name, url });

          // Voeg een optie toe aan de dropdown
          const option = document.createElement('option');
          option.value = url;
          option.textContent = toegestaneMap.get(entry.name); // gebruik het label uit de map
          fileList.appendChild(option);
        }
      }

      // Toon een foutmelding als er geen geldige bestanden zijn
      if (audioFiles.length === 0) {
        errorMessage.textContent = "⚠️ Geen toegestane audio-bestanden gevonden: mismatch tussen audiofiles in datafile en files in selected folder.";
      } else {
        fileList.disabled = false; // activeer de dropdown
      }
    } catch (err) {
      // Foutafhandeling als de gebruiker de selectie annuleert of er iets misgaat
      console.error("Folder selection cancelled or failed:", err);
      errorMessage.textContent = "⚠️ Folder selection was cancelled or failed.";
    }
  });

  // Speel het geselecteerde audiobestand af wanneer de gebruiker een keuze maakt
  fileList.addEventListener('change', () => {
    const selectedUrl = fileList.value;
    audioPlayer.src = selectedUrl;
  });
}


// Luister naar custom event van Dash
window.addEventListener("allowedFilesReady", function (e) {
  const allowedFiles = e.detail;
  if (Array.isArray(allowedFiles)) {
    initAudioSelector(allowedFiles);
  } else {
    console.error("Ongeldige data ontvangen voor toegestane bestanden.");
  }
});
