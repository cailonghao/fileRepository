import html_util

if __name__ == '__main__':
    text = (
        "The Krowor Municipal District was carved out of the Ledzokuku-Krowor"
        " Municipal District in 2018 & it's population is > 200000."
    )

    text = html_util.clear_html_tags(text)
    print(text)
    text = "Bag of rice now cost ₦150000 naira. Ah! 😱 Èdakun o"
    print(html_util.clear_unicode(text))