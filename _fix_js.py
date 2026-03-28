"""Fix renderConfirmationCard to accept an optional answer string."""
import re

with open('frontend/script.js', encoding='utf-8') as fh:
    s = fh.read()

# 1. Update function signature to accept answer parameter
old_sig = 'function renderConfirmationCard(preview) {'
new_sig = 'function renderConfirmationCard(preview, answerText) {'
s = s.replace(old_sig, new_sig, 1)

# 2. Update the hardcoded intro text to use answerText if provided
old_intro = (
    "        contentDiv.innerHTML = `\n"
    "            <p style=\"margin-bottom:10px;color:var(--text-secondary);font-size:0.9rem;\">\n"
    "                Here's what I extracted. Edit any field if needed, then confirm to save.\n"
    "            </p>"
)
new_intro = (
    "        const introText = answerText || \"Here's what I extracted. Edit any field if needed, then confirm to save.\";\n"
    "        contentDiv.innerHTML = `\n"
    "            <p style=\"margin-bottom:10px;color:var(--text-secondary);font-size:0.9rem;\">\n"
    "                ${introText}\n"
    "            </p>"
)
if old_intro in s:
    s = s.replace(old_intro, new_intro, 1)
    print("Fixed intro text")
else:
    print("Intro not found, current intro area:")
    i = s.find("contentDiv.innerHTML")
    print(repr(s[i:i+300]))

# 3. Image upload path: renderConfirmationCard(data) -> renderConfirmationCard(data, null)
old_img = 'renderConfirmationCard(data);'
new_img = "renderConfirmationCard(data, null);"
s = s.replace(old_img, new_img, 1)

# 4. Chat log path: renderConfirmationCard(data.expense) -> pass answer too
old_chat = 'renderConfirmationCard(data.expense);'
new_chat = "renderConfirmationCard(data.expense, data.answer);"
s = s.replace(old_chat, new_chat, 1)

with open('frontend/script.js', 'w', encoding='utf-8', newline='\n') as fh:
    fh.write(s)

print("Done. Checks:")
print("  sig:", "renderConfirmationCard(preview, answerText)" in s)
print("  introText:", "introText" in s)
print("  chat pass:", "renderConfirmationCard(data.expense, data.answer)" in s)
