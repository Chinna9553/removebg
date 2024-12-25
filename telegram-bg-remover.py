import os
import uuid
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from rembg import remove
from PIL import Image
from io import BytesIO

# Constants
API_TOKEN = "7758896390:AAH1QSMCmPvPwsbTV9errbOL8eEfdE-k6fY"  # Replace with your actual Bot API token
OUTPUT_FOLDER = "output_images"

# Ensure the output folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

async def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message when the bot starts."""
    await update.message.reply_text(
        "Welcome! Send me a photo, and I'll remove its background for you!"
    )

async def remove_background(update: Update, context: CallbackContext) -> None:
    """Process the user's image and remove its background."""
    if update.message.photo:
        try:
            # Get the largest photo file
            photo = update.message.photo[-1]
            file = await photo.get_file()
            
            # Generate unique filenames
            input_path = os.path.join(OUTPUT_FOLDER, f"input_{uuid.uuid4()}.jpg")
            output_path = os.path.join(OUTPUT_FOLDER, f"output_{uuid.uuid4()}.png")
            
            # Download the photo
            await file.download_to_drive(input_path)
            
            # Process the image using rembg
            with open(input_path, "rb") as input_file:
                input_image = input_file.read()
                output_image = remove(input_image)
            
            # Save the processed image as a .png file
            with open(output_path, "wb") as output_file:
                output_file.write(output_image)
            
            # Send the processed image preview back to the user (without the background)
            image_preview = Image.open(BytesIO(output_image))
            bio = BytesIO()
            bio.name = 'processed_image.png'
            image_preview.save(bio, 'PNG')
            bio.seek(0)
            
            # Send the preview image and suggestion message
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

        except Exception as e:
            await update.message.reply_text(
                f"An error occurred while processing your image: {e}"
            )
    else:
        await update.message.reply_text("Please send me a photo!")

def main() -> None:
    """Run the bot."""
    application = ApplicationBuilder().token(API_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    
    # Photo handler
    application.add_handler(MessageHandler(filters.PHOTO, remove_background))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
