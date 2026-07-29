import base64
import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

# API Key របស់អ្នក
VIRUSTOTAL_API_KEY = "6426cba236fc8efbf78e3cb7c09972ae9d07e42cdf5f9d14fc84f396cbaa0710"

# កូដ Regex សម្រាប់ចាប់យក URL
URL_REGEX = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

# មុខងារពេលអ្នកប្រើប្រាស់ចុច /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_message = (
        f"សួស្តី {user_name}! 🙏\n\n"
        "ខ្ញុំជា Bot ត្រួតពិនិត្យសុវត្ថិភាពតំណភ្ជាប់ (Link Security Bot)។\n"
        "សូមផ្ញើ Link ណាមួយដែលអ្នកមានការសង្ស័យមកកាន់ខ្ញុំ ខ្ញុំនឹងជួយឆែកជាមួយប្រព័ន្ធ VirusTotal ជូនអ្នកភ្លាមៗ!"
    )
    await update.message.reply_text(welcome_message)

# មុខងារឆែក Link ជាមួយ VirusTotal API
def check_url_with_virustotal(url):
    try:
        # VirusTotal API v3 តម្រូវឱ្យ encode URL ជា base64 (ដកសញ្ញា = ចេញ)
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
        endpoint = f"https://www.virustotal.com/api/v3/urls/{url_id}"
        
        headers = {
            "x-apikey": VIRUSTOTAL_API_KEY
        }
        
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            result = response.json()
            stats = result['data']['attributes']['last_analysis_stats']
            
            malicious = stats.get('malicious', 0)
            suspicious = stats.get('suspicious', 0)
            
            if malicious > 0 or suspicious > 0:
                return True, f"រកឃើញគ្រោះថ្នាក់! (Malicious: {malicious}, Suspicious: {suspicious})"
            else:
                return False, "មានសុវត្ថិភាព (មិនមានការរកឃើញមេរោគ)"
        else:
            # បើមិនទាន់មានក្នុងទិន្នន័យ VirusTotal អាចធ្វើការ Submit ឆែកថ្មី ឬถือថាធម្មតា
            return False, "មិនមានទិន្នន័យគ្រោះថ្នាក់ក្នុងប្រព័ន្ធ VirusTotal ទេ"
    except Exception as e:
        return False, f"កំហុសបច្ចេកទេស៖ {str(e)}"

# មុខងារពេលអ្នកប្រើប្រាស់ផ្ញើ Link មកកាន់ Bot
async def check_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message and message.text:
        urls = re.findall(URL_REGEX, message.text)
        
        if urls:
            target_url = urls[0]
            
            # ផ្ញើសារប្រាប់ថា Bot កំពុងឆែក
            processing_msg = await message.reply_text(f"⏳ កំពុងពិនិត្យមើល Link ຜ່ານ VirusTotal:\n`{target_url}`\nសូមរង់ចាំបន្តិច...")
            
            # ហៅមុខងារឆែក VirusTotal
            is_dangerous, analysis_msg = check_url_with_virustotal(target_url)
            
            if is_dangerous:
                result_text = f"🚨 **ប្រយ័ត្នខ្ពស់!** Link នេះត្រូវបានរកឃើញថាមាន **គ្រោះថ្នាក់ (Phishing/Malware)**!\n\n📋 **ព័ត៌មានលម្អិត:** {analysis_msg}\n❌ សូមកុំចុចលើ Link នេះឱ្យសោះ!"
            else:
                result_text = f"✅ **សុវត្ថិភាព:** Link នេះមិនទាន់រកឃើញសញ្ញាគ្រោះថ្នាក់ទេ។\n\n🛡 **ស្ថានភាព៖** {analysis_msg}"
            
            # កែប្រែសារដើមបង្ហាញលទ្ធផល
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=processing_msg.message_id,
                text=result_text,
                parse_mode="Markdown"
            )
        else:
            await message.reply_text("⚠️ សូមផ្ញើតែតំណភ្ជាប់ (URL) ដែលមានទម្រង់ត្រឹមត្រូវ (ឧទាហរណ៍៖ https://example.com) ដើម្បីឱ្យខ្ញុំជួយពិនិត្យ។")

def main():
    # ដាក់ Telegram Bot Token របស់អ្នកដែលបានពី @BotFather ទីនេះ
    TOKEN = "8872839744:AAH_74N78MQreUl1V-rnFxJ-2PHgNBu-jKc"
    
    app = ApplicationBuilder().token(TOKEN).build()

    # Handler សម្រាប់ពាក្យបញ្ជា /start
    app.add_handler(CommandHandler("start", start))
    
    # Handler សម្រាប់ចាប់យករាល់សារអត្ថបទ
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_link))

    print("Bot ត្រួតពិនិត្យ Link ជាមួយ VirusTotal កំពុងដំណើរការ...")
    app.run_polling()

if __name__ == '__main__':
    main()