import re

from pyrogram import Client, filters

from re import search, sub, finditer, compile
import warnings

import time

__module_info__ = {
    'name': 'Keyboard Layout Correction',
    'author': ['pelmeshke', '@pelmeshke'],
    'version': 'v1.1',
    'description': 'Autocorrecting wrong layout. Doesn\'t working so accuracy that want to be',
    'commands': {
        ('.fromeng', '.from_eng', '.translayout', '/fromeng', '/from_eng', '/translayout'): {
            'desc': 'Translating from english layout to russian. Command doesn\'t take any args',
            'func': 'command([\'fromeng\', \'from_eng\', \'translayout\'], [\'.\', \'/\'])'
        },
        ('.fromrus', '.from_rus', '/fromrus', '/from_rus'): {
            'desc': 'Translating from russian layout to english. Command doesn\'t take any args',
            'func': 'command([\'fromrus\', \'from_rus\'], [\'.\', \'/\'])'
        },
        ('.autocorrlayout', '/autocorrlayout', '.acl', '/acl'): {
            'desc': 'Turning on or off autocorrection. Command doesn\'t take any args',
            'func': 'command([\'autocorrlayout\', \'acl\'], [\'.\', \'/\'])'
        }
    },
    'dependencies': ['russian_frequency_dictionary.txt', 'english_frequency_dictionary.txt'],
    'changelog': {'v1.1': 'Added translate from russian layout to english'}
}

RUS = 'ё1234567890-=йцукенгшщзхъ\\фывапролджэячсмитьбю.Ё!"№;%:?*()_+ЙЦУКЕНГШЩЗХЪ/ФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,'
ENG = '`1234567890-=qwertyuiop[]\\asdfghjkl;\'zxcvbnm,./~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:"ZXCVBNM<>?'
missed_rus_in_eng = r'\`\[\]\;\'\,\.\~\{\}\:"\<\>'
word_regex = f'(([A-Za-z{missed_rus_in_eng}]+)|(\w+))'

vowels = 'аоыуэиеёюя'
consonants = 'бвгджзйклмнпрстфхцчшщ'


def rus_to_eng(symbol):
    if symbol in RUS:
        index = RUS.index(symbol)
        return ENG[index]
    else:
        return symbol


def eng_to_rus(symbol):
    if symbol in ENG:
        index = ENG.index(symbol)
        return RUS[index]
    else:
        return symbol


def rus_text_to_eng(text):
    str_ = ''

    for i in text:
        str_ += rus_to_eng(i)
    return str_


def eng_text_to_rus(text):
    str_ = ''

    for i in text:
        str_ += eng_to_rus(i)
    return str_


def percent_rus_in_text(text):
    length = len(text)
    rus_in_text = 0
    for i in text:
        rus_in_text += i in RUS
    return rus_in_text / length if length > 0 else 1


def percent_eng_in_text(text):
    length = len(text)
    eng_in_text = 0
    for i in text:
        eng_in_text += i in ENG
    return eng_in_text / length if length > 0 else 1


try:
    RUSSIAN_DICTIONARY_FILE_NAME = 'C:\\Users\\BigBro\\PycharmProjects\\peluserbot\\resources\\russian_frequency_dictionary.txt'
    RUSSIAN_DICTIONARY = open(RUSSIAN_DICTIONARY_FILE_NAME, 'r', encoding='utf8').read().split('\n')
except:
    warnings.warn('Russian frequency dictionary not found. Module will work but accuracy will be lower')
    RUSSIAN_DICTIONARY = None

try:
    ENGLISH_DICTIONARY_FILE_NAME = 'C:\\Users\\BigBro\\PycharmProjects\\peluserbot\\resources\\english_frequency_dictionary.txt'
    ENGLISH_DICTIONARY = open(ENGLISH_DICTIONARY_FILE_NAME, 'r', encoding='utf8').read().split('\n')
except:
    warnings.warn('English frequency dictionary not found. Module will work but accuracy will be lower')
    ENGLISH_DICTIONARY = None


def get_russian_words_rate(text):
    if RUSSIAN_DICTIONARY is None:
        return 1

    words = list(finditer(compile(word_regex), text.lower()))
    count_words = 0

    for i in words:
        if i.group(1) in RUSSIAN_DICTIONARY:
            count_words += 1

    return (count_words / len(words)) if len(words) > 0 else 0


def get_english_words_rate(text):
    if ENGLISH_DICTIONARY is None:
        return 1

    words = list(finditer(compile(word_regex), text.lower()))
    count_words = 0

    for i in words:
        if i.group(1) in ENGLISH_DICTIONARY:
            count_words += 1

    return (count_words / len(words)) if len(words) > 0 else 0


def is_eng_layout(text):
    text = sub(r'(@\w+)', '', text)

    count = sum([len(i.group(1)) for i in finditer(compile(word_regex), text)])
    words = ' '.join([i.group(1) for i in finditer(compile(word_regex), text)])
    count_right_combs = 0
    count_wrong_combs = 0

    count_right_combs += 2 * len(re.findall(rf'([{consonants}][{vowels}])', words))
    count_wrong_combs += 2 * len(re.findall(rf'([{consonants}][{vowels}])', eng_text_to_rus(words)))

    is_combs_equal = count_right_combs == count_wrong_combs and count_wrong_combs > 0
    combs_in_text_condition = count_wrong_combs >= .40 * count

    is_not_command = not search(r'^[/.]\w+', text)

    russian_words_rate_in_text = get_russian_words_rate(text)
    russian_words_rate_in_translated_text = get_russian_words_rate(eng_text_to_rus(text))

    english_words_rate_in_text = get_english_words_rate(text)

    rus_in_text = percent_rus_in_text(text)
    eng_in_text = percent_eng_in_text(text)

    print(words, eng_text_to_rus(text), russian_words_rate_in_text, russian_words_rate_in_translated_text,
          english_words_rate_in_text,
          count_right_combs, count_wrong_combs, is_not_command)

    return english_words_rate_in_text < 0.6 and \
           (russian_words_rate_in_translated_text > 0.6 and russian_words_rate_in_text < 0.1 or
            not is_combs_equal and combs_in_text_condition) and \
           is_not_command and not (rus_in_text > 0.1 and eng_in_text > 0.1)


def is_layout_incorrect_and_english(text):
    text = text.lower()
    words = [i.group(1) for i in finditer(compile(word_regex), text)]
    words_count = len(words)
    words_text = ' '.join(words)

    is_command = search(r'^[/.]\w+', text)
    if is_command:
        return False

    # searching syllables
    count_right_combs = len(re.findall(rf'([{consonants}][{vowels}])', words_text))
    count_wrong_combs = len(re.findall(rf'([{consonants}][{vowels}])', eng_text_to_rus(words_text)))

    syllables_score = 1 - (count_wrong_combs - count_right_combs) / count_wrong_combs

    russian_words_rate = get_russian_words_rate(text)
    english_words_rate = get_english_words_rate(text)
    russian_words_rate_in_translated_text = get_english_words_rate(eng_text_to_rus(text))


    print(syllables_score, russian_words_rate, english_words_rate)

    return syllables_score <= 0.21 and russian_words_rate_in_translated_text >= english_words_rate and \
           russian_words_rate <= 0.2


def layout_filter(flt, peluserbot, message):
    try:
        if not hasattr(peluserbot, 'is_correcting_layout'):
            peluserbot.is_correcting_layout = True

        if bool(message.from_user and message.from_user.is_self or message.outgoing) and \
                message.text and peluserbot.is_correcting_layout:
            return is_layout_incorrect_and_english(message.text)
    except Exception as e:
        print(repr(e))

    return False


@Client.on_message(filters.text & (filters.command(['fromeng', 'from_eng', 'translayout'], ['.', '/'])))
async def translate_english_layout(peluserbot, message):
    try:
        if message.reply_to_message is None:
            if bool(message.from_user and message.from_user.is_self or message.outgoing) and message.text:
                await message.edit_text('<b>There isn\'t reply message. Reply command to the message</b>')
            else:
                await message.reply_text('<b>There isn\'t reply message. Reply command to the message</b>')

        elif bool(message.reply_to_message.from_user and
                  message.reply_to_message.from_user.is_self or
                  message.reply_to_message.outgoing) and \
                message.reply_to_message.text and \
                is_eng_layout(message.reply_to_message.text):

            await message.reply_to_message.edit_text(eng_text_to_rus(message.reply_to_message.text), parse_mode='html')
        else:
            await message.reply_text(eng_text_to_rus(message.reply_to_message.text), parse_mode='html')

    except Exception as e:
        print(repr(e))


@Client.on_message(filters.text & (filters.command(['fromrus', 'from_rus'], ['.', '/'])))
async def translate_russian_layout(peluserbot, message):
    try:
        if message.reply_to_message is None:
            if bool(message.from_user and message.from_user.is_self or message.outgoing) and message.text:
                await message.edit_text('<b>There isn\'t reply message. Reply command to the message</b>')
            else:
                await message.reply_text('<b>There isn\'t reply message. Reply command to the message</b>')

        elif bool(message.reply_to_message.from_user and
                  message.reply_to_message.from_user.is_self or
                  message.reply_to_message.outgoing) and \
                message.reply_to_message.text and \
                not is_eng_layout(message.reply_to_message.text):

            await message.reply_to_message.edit_text(rus_text_to_eng(message.reply_to_message.text), parse_mode='html')
        else:
            await message.reply_text(rus_text_to_eng(message.reply_to_message.text), parse_mode='html')

    except Exception as e:
        print(repr(e))


@Client.on_message(filters.me & filters.text & filters.command(['autocorrlayout', 'acl'], ['.', '/']))
async def turning_corrention_layout(peluserbot, message):
    try:
        if not hasattr(peluserbot, 'is_correcting_layout'):
            peluserbot.is_correcting_layout = True

        if peluserbot.is_correcting_layout:
            peluserbot.is_correcting_layout = False
            await message.edit_text('<b>Layout autocorrection turned off</b>')
        else:
            peluserbot.is_correcting_layout = True
            await message.edit_text('<b>Layout autocorrection turned on</b>')

    except Exception as e:
        print(repr(e))


@Client.on_message(filters.me & filters.text & filters.create(func=layout_filter))
async def corrention_layout(peluserbot, message):
    try:
        await message.edit_text(eng_text_to_rus(message.text))
    except Exception as e:
        print(repr(e))


if __name__ == '__main__':
    strings = [
        'bought me a boat',
        'He deserve it because he is so cool',
        'Put your head on my shoulder',
        'not me',
        'uidjfldkhgklsdhkjgfhgjfdjk',
        'lsdfjdlskfhd;sghdlhl;kj',
        'это очень просто',
        'да',
        'ну знаешь, это было бы слишком просто, он бы не сделал так',
        'прецессия спутника из-за пертурбации была увеличена, поэтому эксцентриситет увеличился',
        'лводадлвопдлыаоплдваодлваодлыоадлыо',
        'воыдлвыодфэзухцкрущш 4835849 влвыллад',
        'В языке Python это называет инкапсуляцией',
        'He said me привет and i dont now what does is mean',
        'kflyj',
        'ns pyftim? xnj \'nj  ghjcnj',
        ',skj yt cjdthityyj',
        'ye kflyj d ghbywbgt',
        ',kznm',
    ]
    for i in strings:
        print(i)
        print(is_eng_layout(i))
        print(is_layout_incorrect_and_english(i))
        print()
