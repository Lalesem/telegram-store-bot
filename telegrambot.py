import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================
# REPLACE THESE WITH YOUR ACTUAL VALUES
BOT_TOKEN = "8029340008:AAFcOx4dbBen9UVDUvlc7LDfmW4usjaHCYI"  # From BotFather
CHANNEL_ID = "-1003615431877"  # Your channel ID (negative number)
ADMIN_IDS = [6094100130 , 8029340008] #Telegram user IDs

# Adult content keywords (comprehensive list)
BLOCKED_KEYWORDS = [
    # Explicit terms
    'porn', 'sex', 'xxx', 'nude', 'naked', 'adult', 'nsfw',
    'escort', 'prostitute', 'viagra', 'cialis', 'erotic',
    'fetish', 'hentai', 'camgirl', 'onlyfans', 'webcam',
    # Common variations
    'p0rn', 'p*rn', 's3x', 's*x', 'sexx', 'pr0n',
    # Dating/hookup related
    'hookup', 'dating', 'meet singles', 'hot singles',
    # Gambling
    'casino', 'poker', 'betting', 'gambling',
    # Drugs
    'marijuana', 'cannabis', 'weed', 'cocaine', 'drug',
    # Add more as needed
]

# Blocked domains
BLOCKED_DOMAINS = [
    'pornhub.com', 'xvideos.com', 'xnxx.com', 'redtube.com',
    'youporn.com', 'xhamster.com', 'chaturbate.com',
    'onlyfans.com', 'manyvids.com',
    # Add more as needed
]


# ==================== HELPER FUNCTIONS ====================

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS


def contains_blocked_content(text: str) -> tuple[bool, str]:
    """
    Check if text contains blocked keywords or domains
    Returns: (is_blocked, reason)
    """
    if not text:
        return False, ""

    text_lower = text.lower()

    # Check for blocked keywords
    for keyword in BLOCKED_KEYWORDS:
        if keyword in text_lower:
            return True, f"Blocked keyword detected: '{keyword}'"

    # Check for URLs and blocked domains
    url_pattern = r'https?://(?:www\.)?([^\s/]+)'
    urls = re.findall(url_pattern, text_lower)

    for url in urls:
        for blocked_domain in BLOCKED_DOMAINS:
            if blocked_domain in url:
                return True, f"Blocked domain detected: '{blocked_domain}'"

    return False, ""


def extract_urls(text: str) -> list:
    """Extract all URLs from text"""
    url_pattern = r'https?://[^\s]+'
    return re.findall(url_pattern, text)


# ==================== BOT COMMANDS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user

    welcome_text = f"""
👋 **Welcome to the Store Bot, {user.first_name}!**

🛍️ **How to use this bot:**

📝 **Submit a Product:**
Simply send a message with:
- Product name
- Description
- Price
- Product link
- Photo (optional)

✅ **What's Allowed:**
- E-commerce products
- Physical goods
- Digital products
- Service offerings
- Valid product links

❌ **What's NOT Allowed:**
- Adult content
- Illegal items
- Gambling/betting
- Drugs or controlled substances
- Spam or scam links

⚠️ All submissions are reviewed before posting to the channel.

**Send your product now!**
"""

    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
📚 **Bot Commands:**

/start - Start the bot
/help - Show this help message
/stats - View bot statistics (Admin only)
/approve [msg_id] - Approve a message (Admin only)
/reject [msg_id] - Reject a message (Admin only)

**How to Submit Products:**
1. Send your product details in one message
2. Include product link and price
3. Add photos if available
4. Wait for admin approval

**Example:**
```
🏷️ Product: iPhone 15 Pro Max
💰 Price: $1,299
📝 Description: Brand new, sealed
🔗 Link: https://yourstore.com/iphone
```

For support, contact the admins.
"""

    await update.message.reply_text(help_text, parse_mode='Markdown')


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics (Admin only)"""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("⛔ This command is only for admins.")
        return

    # Get statistics from context
    total_submissions = context.bot_data.get('total_submissions', 0)
    approved = context.bot_data.get('approved', 0)
    rejected = context.bot_data.get('rejected', 0)
    blocked = context.bot_data.get('blocked', 0)

    stats_text = f"""
📊 **Bot Statistics**

📥 Total Submissions: {total_submissions}
✅ Approved: {approved}
❌ Rejected: {rejected}
🚫 Auto-Blocked: {blocked}

⏰ Uptime: Active
"""

    await update.message.reply_text(stats_text, parse_mode='Markdown')


# ==================== MESSAGE HANDLERS ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages from users"""
    user = update.effective_user
    message = update.message

    # Initialize bot_data counters if not exist
    if 'total_submissions' not in context.bot_data:
        context.bot_data['total_submissions'] = 0
        context.bot_data['approved'] = 0
        context.bot_data['rejected'] = 0
        context.bot_data['blocked'] = 0

    context.bot_data['total_submissions'] += 1

    # Get message text and caption
    text = message.text or message.caption or ""

    # Check for blocked content
    is_blocked, reason = contains_blocked_content(text)

    if is_blocked:
        context.bot_data['blocked'] += 1
        await message.reply_text(
            f"⛔ **Content Blocked!**\n\n"
            f"Reason: {reason}\n\n"
            f"Your submission contains prohibited content. "
            f"Please review our guidelines and try again.",
            parse_mode='Markdown'
        )

        # Notify admins about blocked content
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"🚫 **Auto-Blocked Content**\n\n"
                         f"User: {user.first_name} (@{user.username})\n"
                         f"User ID: {user.id}\n"
                         f"Reason: {reason}\n\n"
                         f"Content: {text[:200]}...",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Error notifying admin: {e}")

        return

    # Create approval buttons for admins
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{message.message_id}_{user.id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{message.message_id}_{user.id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Store message data for later approval
    context.bot_data[f"pending_{message.message_id}_{user.id}"] = {
        'user_id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'text': text,
        'photo': message.photo[-1].file_id if message.photo else None,
        'document': message.document.file_id if message.document else None,
    }

    # Forward to admins for approval
    for admin_id in ADMIN_IDS:
        try:
            admin_text = f"""
📦 **New Product Submission**

👤 From: {user.first_name} (@{user.username or 'N/A'})
🆔 User ID: {user.id}

📝 **Content:**
{text}

**Review and approve or reject below:**
"""

            if message.photo:
                await context.bot.send_photo(
                    chat_id=admin_id,
                    photo=message.photo[-1].file_id,
                    caption=admin_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            elif message.document:
                await context.bot.send_document(
                    chat_id=admin_id,
                    document=message.document.file_id,
                    caption=admin_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error sending to admin {admin_id}: {e}")

    # Confirm submission to user
    await message.reply_text(
        "✅ **Submission Received!**\n\n"
        "Your product has been submitted for review.\n"
        "You'll be notified once it's approved and posted to the channel.\n\n"
        "⏰ Review typically takes 5-30 minutes.",
        parse_mode='Markdown'
    )


# ==================== CALLBACK HANDLERS ====================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle approval/rejection callbacks"""
    query = update.callback_query
    admin_id = query.from_user.id

    if not is_admin(admin_id):
        await query.answer("⛔ You don't have permission to do this.", show_alert=True)
        return

    await query.answer()

    # Parse callback data
    action, message_id, user_id = query.data.split('_')
    message_key = f"pending_{message_id}_{user_id}"

    # Get stored message data
    message_data = context.bot_data.get(message_key)

    if not message_data:
        await query.edit_message_text("❌ Message data not found. It may have been processed already.")
        return

    user_id = int(user_id)

    if action == "approve":
        # Post to channel
        try:
            channel_text = f"{message_data['text']}\n\n➡️ Submitted by: @{message_data['username'] or message_data['first_name']}"

            if message_data['photo']:
                await context.bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=message_data['photo'],
                    caption=channel_text
                )
            elif message_data['document']:
                await context.bot.send_document(
                    chat_id=CHANNEL_ID,
                    document=message_data['document'],
                    caption=channel_text
                )
            else:
                await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=channel_text
                )

            context.bot_data['approved'] = context.bot_data.get('approved', 0) + 1

            # Notify user
            await context.bot.send_message(
                chat_id=user_id,
                text="🎉 **Congratulations!**\n\n"
                     "Your product has been approved and posted to the channel!\n\n"
                     "Thank you for your submission! 🛍️",
                parse_mode='Markdown'
            )

            # Update admin message
            await query.edit_message_text(
                f"✅ **APPROVED by {query.from_user.first_name}**\n\n"
                f"Posted to channel successfully!\n\n"
                f"{query.message.text or query.message.caption}"
            )

        except Exception as e:
            logger.error(f"Error posting to channel: {e}")
            await query.edit_message_text(f"❌ Error posting to channel: {str(e)}")

    elif action == "reject":
        context.bot_data['rejected'] = context.bot_data.get('rejected', 0) + 1

        # Notify user
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ **Submission Rejected**\n\n"
                 "Your product submission was not approved.\n\n"
                 "Possible reasons:\n"
                 "- Doesn't meet quality standards\n"
                 "- Missing important information\n"
                 "- Inappropriate content\n\n"
                 "Please review and submit again if appropriate.",
            parse_mode='Markdown'
        )

        # Update admin message
        await query.edit_message_text(
            f"❌ **REJECTED by {query.from_user.first_name}**\n\n"
            f"{query.message.text or query.message.caption}"
        )

    # Remove from pending
    del context.bot_data[message_key]


# ==================== ERROR HANDLER ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")


# ==================== MAIN FUNCTION ====================

def main():
    """Start the bot"""

    # Validate configuration
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Please set your BOT_TOKEN in the code!")
        print("Get it from @BotFather on Telegram")
        return

    if CHANNEL_ID == "-1001234567890":
        print("❌ ERROR: Please set your CHANNEL_ID in the code!")
        print("Get it by forwarding a channel message to @userinfobot")
        return

    if ADMIN_IDS == [123456789]:
        print("⚠️  WARNING: Please set your ADMIN_IDS in the code!")
        print("Add your Telegram user ID to the ADMIN_IDS list")

    print("🤖 Starting Telegram Store Bot...")
    print(f"📢 Channel ID: {CHANNEL_ID}")
    print(f"👥 Admin IDs: {ADMIN_IDS}")
    print("✅ Bot is running! Press Ctrl+C to stop.\n")

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))

    # Handle all text and photo messages
    application.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.Document.ALL,
        handle_message
    ))

    # Handle callback queries (approve/reject buttons)
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Error handler
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()