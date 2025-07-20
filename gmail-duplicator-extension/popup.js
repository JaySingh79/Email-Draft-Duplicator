document.addEventListener('DOMContentLoaded', async () => {
  const checkBtn = document.getElementById('checkServer');
  const statusEl = document.getElementById('serverStatus');
  const draftSelect = document.getElementById('draftSelect');
  const copyCount = document.getElementById('copyCount');
  const duplicateBtn = document.getElementById('duplicateBtn');
  const messageEl = document.getElementById('message');

  // Function to check server status
  async function checkServerStatus() {
    statusEl.textContent = '🔄 Checking server...';
    try {
      const res = await fetch('http://localhost:5000/status');
      if (!res.ok) throw new Error('Status not OK');
      const json = await res.json();
      if (json.status === 'Ok') {
        statusEl.textContent = '✅ Server is running. Loading drafts...';
        await loadDrafts(); // Load drafts immediately after success
      } else {
        statusEl.textContent = '⚠️ Unexpected server response.';
      }
    } catch (err) {
      statusEl.textContent = '❌ Server not running. Run the server file';
    }
  }

  // Function to load drafts from server
  async function loadDrafts() {
    draftSelect.innerHTML = ''; // Clear any existing options
    try {
      const res = await fetch('http://localhost:5000/list_drafts');
      const data = await res.json();
      if (data.status !== 'success') throw new Error('Draft fetch failed');

      data.drafts.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.id;
        opt.textContent = `[${d.id.slice(0, 8)}…] ${d.subject}`;
        draftSelect.appendChild(opt);
      });

      if (data.drafts.length === 0) {
        statusEl.textContent = '⚠️ No drafts found in Gmail.';
      }
    } catch (err) {
      statusEl.textContent = '❌ Failed to fetch drafts. Is Gmail authenticated?';
    }
  }

  // Function to request duplication
  async function duplicateDraft() {
    const draftId = draftSelect.value;
    const count = parseInt(copyCount.value);

    if (!draftId || !count || count < 1) {
      messageEl.textContent = '❌ Please select a draft and a valid count.';
      return;
    }

    duplicateBtn.disabled = true;
    messageEl.textContent = '⏳ Duplicating drafts...';

    try {
      const res = await fetch('http://localhost:5000/duplicate_draft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ draft_id: draftId, copies: count })
      });

      const data = await res.json();
      if (data.status === 'success') {
        messageEl.textContent = `✅ Successfully duplicated draft ${count} times.`;
      } else {
        messageEl.textContent = '❌ Duplication failed.';
      }
    } catch (err) {
      messageEl.textContent = '❌ Error duplicating draft.';
    } finally {
      duplicateBtn.disabled = false;
    }
  }

  // Bind button events
  checkBtn.addEventListener('click', checkServerStatus);
  duplicateBtn.addEventListener('click', duplicateDraft);
});
