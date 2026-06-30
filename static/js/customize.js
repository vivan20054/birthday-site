const messagesWrap = document.getElementById('messagesWrap');
const addMessageBtn = document.getElementById('addMessageBtn');
const randomizeBtn = document.getElementById('randomizeBtn');
const form = document.getElementById('partyForm');

addMessageBtn?.addEventListener('click', () => {
  const row = document.createElement('div');
  row.className = 'message-row';
  row.innerHTML = `
    <input type="text" name="sender_name[]" placeholder="Sender name" required />
    <textarea name="message_text[]" rows="3" placeholder="Write a loving message" required></textarea>
  `;
  messagesWrap.appendChild(row);
});

randomizeBtn?.addEventListener('click', async () => {
  const recipient = form.querySelector('input[name="recipient_name"]').value || 'Bestie';
  randomizeBtn.disabled = true;
  randomizeBtn.textContent = 'Creating vibe...';
  try {
    const res = await fetch(`/api/randomize?recipient=${encodeURIComponent(recipient)}`);
    const data = await res.json();

    form.querySelector('input[name="title"]').value = data.title;
    form.querySelector('input[name="subtitle"]').value = data.subtitle;
    form.querySelector('textarea[name="intro_text"]').value = data.intro_text;
    form.querySelector('input[name="accent_color"]').value = data.accent_color;
    form.querySelector('input[name="secondary_color"]').value = data.secondary_color;
    form.querySelector('select[name="background_style"]').value = data.background_style;
    form.querySelector('input[name="surprise_prompt"]').value = data.surprise_prompt;

    messagesWrap.innerHTML = '';
    data.messages.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'message-row';
      row.innerHTML = `
        <input type="text" name="sender_name[]" placeholder="Sender name" required value="${item.sender}" />
        <textarea name="message_text[]" rows="3" placeholder="Write a loving message" required>${item.text}</textarea>
      `;
      messagesWrap.appendChild(row);
    });
  } catch (error) {
    alert('Could not randomize right now. Please try again.');
  } finally {
    randomizeBtn.disabled = false;
    randomizeBtn.textContent = 'Randomize with AI vibe';
  }
});
