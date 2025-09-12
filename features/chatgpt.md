---
title: ChatGPT Feature
permalink: /features/chatgpt
---

{% comment %}Inlined from docs/FEATURES/chatgpt.md{% endcomment %}
# ChatGPT Integration

## Overview

The bot integrates OpenAI's GPT-4 and DALL·E 3 to provide AI-powered interactions, conversations, and image generation.

## Features

### 💬 Conversation Threads

Create persistent chat threads with memory:

- **Start**: `!chat <your message>`
- **Continue**: Just type in the thread (no prefix needed)
- **End**: `!endchat` in the thread
- **Memory**: Bot remembers last 20 messages in conversation
- **Retention**: Configurable (default 7 days)

#### Thread Features
- Auto-archives after retention period
- Admins can end any thread
- Users can only end their own threads
- Thread list with `!mythreads`
- Admin view with `!allthreads`

### 🎯 Quick Commands

One-off AI interactions without creating threads:

#### Feel-Good Messages (`!feelgood`)
- 50-word uplifting messages
- Can target specific recipients
- Example: `!feelgood @friend`

#### Jokes (`!joke`)
- Family-friendly humor
- Topic-specific jokes available
- Example: `!joke programming`

#### Compliments (`!compliment`)
- Wholesome, personalized compliments
- Can specify topic
- Example: `!compliment @user about their art`

#### Advice (`!advice`)
- Thoughtful, constructive advice
- Topic-specific guidance
- Example: `!advice time management`

#### Inspiration (`!inspo`)
- Original inspirational quotes
- Can address specific people
- Example: `!inspo team`

#### Quick Questions (`!q`)
- Fast AI responses
- No thread creation
- Example: `!q explain quantum computing simply`

### 🎨 Image Generation

Create images using DALL·E 3:

- **Command**: `!image <description>`
- **Size**: 1024x1024 pixels
- **Format**: Direct URL response
- **Limits**: Follows OpenAI content policy

#### Examples:
```
!image a serene Japanese garden with cherry blossoms
!image cyberpunk city at night with neon lights
!image cute cartoon dragon reading a book
```

## Configuration

### Token Limits

Control response length per command:

```json
"max_tokens": {
	"feelgood": 50,
	"joke": 75,
	"compliment": 50,
	"advice": 100,
	"inspo": 50,
	"query": 150
}
```

### Custom Prompts

Customize AI behavior:

```json
"prompts": {
	"joke": {
		"generic": "Tell a family-friendly joke.",
		"targeted": "Tell a family-friendly joke about {topic}."
	}
}
```

### Thread Retention

Set how long threads are kept:

- Command: `!setchatretention <time>`
- Formats: `7d`, `24h`, `3d12h`
- Default: 7 days

## Best Practices

### For Users
1. **Be specific** in your requests
2. **Use threads** for longer conversations
3. **End threads** when done to save resources
4. **Report issues** with inappropriate responses

### For Admins
1. **Monitor usage** with token display
2. **Set appropriate limits** for your community
3. **Customize prompts** to match server culture
4. **Review threads** periodically
5. **Set retention** based on activity level

## Token Usage

When enabled, shows OpenAI API usage:
- Prompt tokens (input)
- Completion tokens (output)
- Total tokens used

Enable with: `!toggletokenusage`

## Limitations

- **Rate limits**: Based on OpenAI API limits
- **Content filtering**: OpenAI's safety systems apply
- **Context length**: ~20 messages in threads
- **Image generation**: 1 image per request

## Troubleshooting

### Common Issues

**"Sorry, I couldn't generate a response"**
- Check OpenAI API key
- Verify API quota
- Check error logs

**Thread not responding**
- Verify it's a chat thread with `!mythreads`
- Check if thread is expired
- Try `!endchat` and create new thread

**Image generation fails**
- Check content policy compliance
- Verify API access to DALL·E
- Try simpler descriptions