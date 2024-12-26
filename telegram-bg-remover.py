import os
import uuid
import logging
import asyncio

try:
    from telegram import Update
    from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
    from rembg import remove
    from PIL import Image
    from io import BytesIO
except ModuleNotFoundError as e:
    print(f"Module not found: {e}. Please ensure all required modules are installed.")
    exit(1)

# Constants
API_TOKEN = "7758896390:AAH1QSMCmPvPwsbTV9errbOL8eEfdE-k6fY"  # Replace with your actual Bot API token
OUTPUT_FOLDER = "output_images"

# Ensure the output folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.webp']

async def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message when the bot starts."""
    try:
        logger.info("Start command received from user %s", update.effective_user.id)
        await update.message.reply_text(
            "Welcome! Send me a photo in JPG, JPEG, PNG, or WEBP format, and I'll remove its background for you!"
        )
    except Exception as e:
        logger.error(f"Error in start command: {e}")

async def handle_text_or_unsupported(update: Update, context: CallbackContext) -> None:
    """Handle text messages or unsupported file formats."""
    try:
        if update.message.text:
            logger.info("Text message received from user %s", update.effective_user.id)
            await update.message.reply_text("I can't process text messages. Please send me a valid photo in JPG, JPEG, PNG, or WEBP format!")
        elif update.message.document:
            file_name = update.message.document.file_name
            if not any(file_name.lower().endswith(ext) for ext in SUPPORTED_FORMATS):
                logger.info("Unsupported file format received from user %s", update.effective_user.id)
                await update.message.reply_text(
                    f"Unsupported file format. Supported formats are: {', '.join(SUPPORTED_FORMATS)}. Please try again."
                )
        elif update.message.sticker:
            logger.info("Sticker received from user %s", update.effective_user.id)
            await update.message.reply_text("I can't process stickers. Please send a photo in JPG, JPEG, PNG, or WEBP format!")
        elif update.message.location:
            logger.info("Location received from user %s", update.effective_user.id)
            await update.message.reply_text("I cannot process location data. Please send me a valid photo in JPG, JPEG, PNG, or WEBP format!")
        elif update.message.contact:
            logger.info("Contact received from user %s", update.effective_user.id)
            await update.message.reply_text("I cannot process contact information. Please send me a valid photo in JPG, JPEG, PNG, or WEBP format!")
        else:
            logger.info("Unknown input received from user %s", update.effective_user.id)
            await update.message.reply_text("I can only process images in JPG, JPEG, PNG, or WEBP format. Please send a valid photo!")
    except Exception as e:
        logger.error(f"Error handling unsupported message: {e}")

async def remove_background(update: Update, context: CallbackContext) -> None:
    """Process the user's image and remove its background."""
    if update.message.photo:
        try:
            logger.info("Photo received from user %s", update.effective_user.id)

            # Send initial progress message
            progress_message = await update.message.reply_text("Processing the image: 0%")

            # Get the largest photo file
            photo = update.message.photo[-1]
            file = await photo.get_file()

            # Generate unique filenames
            input_path = os.path.join(OUTPUT_FOLDER, f"input_{uuid.uuid4()}.jpg")
            output_path = os.path.join(OUTPUT_FOLDER, f"output_{uuid.uuid4()}.png")

            # Download the photo
            await file.download_to_drive(input_path)
            logger.info("Photo downloaded to %s", input_path)

            # Update progress to 30%
            await progress_message.edit_text("Processing the image: 30%")

            # Process the image using rembg
            with open(input_path, "rb") as input_file:
                input_image = input_file.read()
                output_image = remove(input_image)

            # Update progress to 70%
            await progress_message.edit_text("Processing the image: 70%")

            # Save the processed image as a .png file
            with open(output_path, "wb") as output_file:
                output_file.write(output_image)

            logger.info("Processed image saved to %s", output_path)

            # Update progress to 100%
            await progress_message.edit_text("Processing the image: 100%")

            # Send the processed image preview back to the user
            bio = BytesIO()
            bio.name = 'processed_image.png'
            bio.write(output_image)
            bio.seek(0)

            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=bio,
                caption="Here's your image preview with the background removed. To retain transparency, please download the PNG below."
            )

            # Provide the download link for the PNG
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=open(output_path, "rb"),
                caption="Download the PNG to keep the transparent background."
            )

            # Cleanup temporary files
            os.remove(input_path)
            os.remove(output_path)
            logger.info("Temporary files deleted.")

        except Exception as e:
            logger.error(f"Error processing photo from user {update.effective_user.id}: {e}")
            await update.message.reply_text(
                f"An error occurred while processing your image: {e}"
            )

async def handle_document(update: Update, context: CallbackContext) -> None:
    """Process image files sent as documents."""
    try:
        file_name = update.message.document.file_name
        if not any(file_name.lower().endswith(ext) for ext in SUPPORTED_FORMATS):
            await update.message.reply_text(
                f"Unsupported file format. Supported formats are: {', '.join(SUPPORTED_FORMATS)}. Please try again."
            )
            return

        progress_message = await update.message.reply_text("Processing the image: 0%")

        file = await update.message.document.get_file()

        # Generate unique filenames
        input_path = os.path.join(OUTPUT_FOLDER, f"input_{uuid.uuid4()}_{file_name}")
        output_path = os.path.join(OUTPUT_FOLDER, f"output_{uuid.uuid4()}.png")

        # Download the document
        await file.download_to_drive(input_path)
        logger.info("Document downloaded to %s", input_path)

        # Update progress to 30%
        await progress_message.edit_text("Processing the image: 30%")

        # Process the image using rembg
        with open(input_path, "rb") as input_file:
            input_image = input_file.read()
            output_image = remove(input_image)

        # Update progress to 70%
        await progress_message.edit_text("Processing the image: 70%")

        # Save the processed image as a .png file
        with open(output_path, "wb") as output_file:
            output_file.write(output_image)

        logger.info("Processed image saved to %s", output_path)

        # Update progress to 100%
        await progress_message.edit_text("Processing the image: 100%")

        # Send the processed image preview back to the user
        bio = BytesIO()
        bio.name = 'processed_image.png'
        bio.write(output_image)
        bio.seek(0)

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=bio,
            caption="Here's your image preview with the background removed. To retain transparency, please download the PNG below."
        )

        # Provide the download link for the PNG
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=open(output_path, "rb"),
            caption="Download the PNG to keep the transparent background."
        )

        # Cleanup temporary files
        os.remove(input_path)
        os.remove(output_path)
        logger.info("Temporary files deleted.")

    except Exception as e:
        logger.error(f"Error processing document from user {update.effective_user.id}: {e}")
        await update.message.reply_text(
            f"An error occurred while processing your file: {e}"
        )

def main() -> None:
    """Run the bot."""
    logger.info("Starting bot...")
    try:
        application = ApplicationBuilder().token(API_TOKEN).build()
    except Exception as e:
        logger.error(f"Failed to initialize bot: {e}")
        exit(1)

    # Command handlers
    application.add_handler(CommandHandler("start", start))

    # Photo handler
    application.add_handler(MessageHandler(filters.PHOTO, remove_background))

    # Document handler for supported formats
    application.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))

    # Text or unsupported message handler
    application.add_handler(MessageHandler(
        filters.TEXT | filters.Document.ALL | filters.VIDEO | filters.LOCATION | filters.CONTACT | filters.VOICE | filters.AUDIO,
        handle_text_or_unsupported
    ))

    try:
        application.run_polling()
    except Exception as e:
        logger.error(f"Bot stopped unexpectedly: {e}")

if __name__ == "__main__":
    main()
