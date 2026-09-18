import subprocess

# Strict YouTube Channel Description limit is 1,000 characters.
# We optimize to ~900-950 characters for maximum SEO keyword density.

desc_1000 = """Welcome to SciBytes (@SciBytesDaily) - your daily source for bite-sized science facts, physics mysteries, and engineering marvels explained in seconds.

We break down complex astrophysics, quantum mechanics, and futuristic technology into fast, engaging educational shorts. From black holes and time dilation to 'What If' scenarios and military aviation, we make science fascinating for everyone.

What We Explore Daily:
- Astrophysics, Black Holes and Deep Space Mysteries
- Quantum Physics, Relativity and Time Dilation
- 'What Happens If' and 'Did You Know' Science Scenarios
- Advanced Engineering, Military Tech and Aviation
- Bizarre Natural Phenomena and Earth Science

Subscribe to SciBytes (@SciBytesDaily) to feed your curiosity every single day!

----------------------------------------
Fair Use Notice: Educational content under Section 107 of US Copyright Act.
Contact: [Your Email]

#SciBytes #Science #Physics #SpaceFacts #Scienceverse #DidYouKnow #Shorts #Astronomy"""

char_count = len(desc_1000)
word_count = len(desc_1000.split())

print(f"Total Characters: {char_count} / 1000 (Limit)")
print(f"Total Words: {word_count}")

assert char_count <= 1000, "Must be within YouTube 1000 character limit!"

# Set to Windows clipboard
process = subprocess.Popen(['powershell', '-Command', 'Set-Clipboard -Value $input'], stdin=subprocess.PIPE, text=True, encoding='utf-8')
process.communicate(input=desc_1000)
print("Updated perfect 1000-char-compliant description copied to clipboard!")
