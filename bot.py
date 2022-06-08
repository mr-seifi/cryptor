import django
from telegram import (Update, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (CallbackContext, Updater, Dispatcher, CommandHandler, ConversationHandler,
                          CallbackQueryHandler)
from telegram import ParseMode
from _helpers.telegram_bot import TelegramService
from django.core.exceptions import ObjectDoesNotExist

django.setup()
from account.models import (User, Trader, Wallet)
from account.views import AccountTelegramView
from account.services import ProfileService
from monitoring.services import ActionService
from monitoring.models import Action
from exchange.models import KuCoin
from secret import BOT_TOKEN


class Main:
    TELEGRAM_MESSAGES = {
        'blind_date': 'سلام، چطوری؟ من کریپتور هستم!',
        'has_not_wallet': 'برای اینکه کارت رو شروع کنی باید ولتت رو به من وصل کنی!',
        'wallet_network': '*شبکه* ولتت چیه؟',
        'wallet_address': '*آدرس* ولتت رو وارد کن.',
        'wallet_failure': 'دوباره تلاش کنید. /menu',
        'wallet_success': 'با موفقیت انجام شد، برای مشاهده منو روی /menu کلیک کنید.',
        'exchange_api_key': 'لطفا *API_KEY* خود را وارد نمایید.',
        'exchange_api_secret': 'لطفا *API_SECRET* خود را وارد نمایید.',
        'exchange_api_passphrase': 'لطفا *API_PASSPHRASE* خود را وارد نمایید.',
        'exchange_success': 'عملیات ثبت صرافی با موفقیت انجام شد. برای مشاهده منو روی /menu کلیک کنید.',
        'exchange_failure': 'دوباره تلاش کنید. /menu'
    }

    TELEGRAM_BUTTONS = {
        'register': 'ثبت‌نام',
        'add_wallet': 'اضافه کردن ولت',
        'add_exchange': 'اتصال به صرافی'
    }

    STATES = {
        'menu': 0,
        'register': 1,
        'wallet': 2,
        'exchange_key': 4,
        'exchange_secret': 5,
        'exchange_passphrase': 6
    }

    @classmethod
    def start(cls, update: Update, context: CallbackContext):
        message = update.message
        user_id = message.from_user

        if TelegramService.who_is(user_id=user_id) == 'anonymous':
            return cls.blind_date(update, context)
        return cls.menu(update, context)

    @classmethod
    def blind_date(cls, update: Update, context: CallbackContext):
        message = update.message
        user_id = message.from_user

        ActionService.cache_action(user_id=user_id,
                                   action=Action.ActionChoices.BLIND_DATE)  # TODO: Rate Limit

        keyboard = [
            [
                InlineKeyboardButton(cls.TELEGRAM_BUTTONS.get('register'), callback_data=cls.STATES['register'])
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message.reply_text(
            cls.TELEGRAM_MESSAGES.get('blind_date'),
            reply_markup=reply_markup
        )

    @classmethod
    def _check_is_not_anonymous(cls, update: Update, context: CallbackContext, user_id):
        if who_is := TelegramService.who_is(user_id=user_id) == 'anonymous':
            return cls.blind_date(update, context)
        return who_is

    @staticmethod
    def _check_has_exchange(user: User) -> bool:
        try:
            user.kucoin
        except ObjectDoesNotExist:
            return False
        else:
            return True

    @staticmethod
    def _check_has_wallet(trader: Trader) -> bool:
        if trader.wallets.exists():
            return True
        return False

    @classmethod
    def initiate_wallet_network(cls, update: Update, context: CallbackContext):
        query = update.callback_query
        user_id = query.from_user

        ActionService.cache_action(user_id=user_id,
                                   action=Action.ActionChoices.INITIATE_WALLET)
        query.answer()

        keyboard = [
            [
                InlineKeyboardButton(Wallet.WalletChoices.labels, callback_data=network)
            ] for network in Wallet.WalletChoices.labels
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        query.edit_message_text(
            cls.TELEGRAM_MESSAGES.get('wallet_network'),
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

        return cls.STATES['wallet']

    @classmethod
    def initiate_wallet_address(cls, update: Update, context: CallbackContext):
        query = update.callback_query
        user_id = query.from_user

        ProfileService.cache_wallet_network(user_id=user_id, wallet_network=query.data)
        query.answer()

        query.edit_message_text(
            cls.TELEGRAM_MESSAGES.get('wallet_address'),
            parse_mode=ParseMode.MARKDOWN
        )

        return cls.STATES['wallet']

    @classmethod
    def done_initiating_wallet_process(cls, update: Update, context: CallbackContext):
        message = update.message
        user_id = message.from_user

        wallet_network = ProfileService.get_wallet_network(user_id=user_id)
        wallet_address = message.text

        # network expired
        if not wallet_network:
            message.reply_text(
                cls.TELEGRAM_MESSAGES.get('wallet_failure')
            )

            return ConversationHandler.END

        trader: Trader = TelegramService.get_queryset(user_id=user_id)
        Wallet.objects.create(trader=trader, network=wallet_network, address=wallet_address)

        message.reply_text(
            cls.TELEGRAM_MESSAGES.get('wallet_success')
        )

        return ConversationHandler.END

    @classmethod
    def initiate_kucoin_api_key(cls, update: Update, context: CallbackContext):
        query = update.callback_query
        user_id = query.from_user

        ActionService.cache_action(user_id=user_id, action=Action.ActionChoices.INITIATE_EXCHANGE)
        query.answer()

        query.edit_message_text(
            cls.TELEGRAM_MESSAGES.get('exchange_api_key'),
            parse_mode=ParseMode.MARKDOWN
        )

        return cls.STATES['exchange_key']

    @classmethod
    def initiate_kucoin_api_secret(cls, update: Update, context: CallbackContext):
        message = update.message
        user_id = message.from_user

        ProfileService.cache_api_key(user_id=user_id, api_key=message.text)

        message.reply_text(
            cls.TELEGRAM_MESSAGES.get('exchange_api_secret'),
            parse_mode=ParseMode.MARKDOWN
        )

        return cls.STATES['exchange_secret']

    @classmethod
    def initiate_kucoin_api_passphrase(cls, update: Update, context: CallbackContext):
        message = update.message
        user_id = message.from_user

        ProfileService.cache_api_secret(user_id=user_id, api_secret=message.text)

        message.reply_text(
            cls.TELEGRAM_MESSAGES.get('exchange_api_passphrase'),
            parse_mode=ParseMode.MARKDOWN
        )

        return cls.STATES['exchange_passphrase']

    @classmethod
    def done_initiating_kucoin_process(cls, update: Update, context: CallbackContext):
        message = update.message
        user_id = message.from_user

        api_key = ProfileService.get_api_key(user_id=user_id)
        api_secret = ProfileService.get_api_secret(user_id=user_id)
        api_passphrase = message.text

        if not api_key:
            message.reply_text(
                cls.TELEGRAM_MESSAGES.get('exchange_failure')
            )

            return ConversationHandler.END

        user = TelegramService.get_queryset(user_id=user_id)
        KuCoin.objects.create(user=user, api_key=api_key, api_secret=api_secret, api_passphrase=api_passphrase)

        message.reply_text(
            cls.TELEGRAM_MESSAGES.get('exchange_success')
        )

        return ConversationHandler.END

    @classmethod
    def menu(cls, update: Update, context: CallbackContext):
        message = update.message
        user_id = message.from_user

        ActionService.cache_action(user_id=user_id,
                                   action=Action.ActionChoices.MENU)  # TODO: Rate Limit For DDOS

        who_is = cls._check_is_not_anonymous(update=update, context=context, user_id=user_id)
        if who_is not in ('user', 'trader'):
            return ConversationHandler.END

        if who_is == 'user':
            user: User = TelegramService.get_queryset(user_id=user_id)
            if not cls._check_has_exchange(user=user):
                keyboard = [
                    [
                        InlineKeyboardButton(cls.TELEGRAM_BUTTONS['add_exchange'],
                                             callback_data=0)
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                message.reply_text(
                    cls.TELEGRAM_MESSAGES.get('has_not_exchange'),
                    reply_markup=reply_markup
                )

                return cls.STATES['exchange_key']
            return AccountTelegramView.user_menu(update=update, context=context)

        else:
            trader: Trader = TelegramService.get_queryset(user_id=user_id)
            # Has not a Wallet
            if not cls._check_has_wallet(trader=trader):
                keyboard = [
                    [
                        InlineKeyboardButton(cls.TELEGRAM_BUTTONS['add_wallet'],
                                             callback_data=0)
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                message.reply_text(
                    cls.TELEGRAM_MESSAGES.get('has_not_wallet'),
                    reply_markup=reply_markup
                )

                return cls.STATES['wallet']
            return AccountTelegramView.trader_menu(update=update, context=context)


def main():
    updater = Updater(token=BOT_TOKEN,
                      use_context=True)

    # Get the dispatcher to register handlers
    dispatcher: Dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', Main.start)
    menu_handler = ConversationHandler(
        entry_points=[CommandHandler('menu', Main.menu)],
        states={

        },
        fallbacks=[CommandHandler('menu', Main.menu)]
    )

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(menu_handler)

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully
    updater.idle()


if __name__ == '__main__':
    main()
