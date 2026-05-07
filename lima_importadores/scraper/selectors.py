
# Google Maps DOM selectors — ALL selectors live here.
# When Google updates the Maps UI, only this file needs to change.
# Prefer data-* and aria-* attributes over generated class names.

# Results panel
RESULTS_PANEL = '[role="feed"]'
LISTING_ITEM = '[role="feed"] div[role="article"]'

# Detail panel fields
DETAIL_NAME = "h1.DUwDvf"
DETAIL_ADDRESS = '[data-item-id="address"] .Io6YTe'
DETAIL_PHONE = '[data-item-id^="phone:tel"] .Io6YTe'
DETAIL_WEBSITE = 'a[data-item-id="authority"]'
DETAIL_RATING = "div.F7nice span[aria-hidden='true']"
DETAIL_REVIEW_COUNT = "div.F7nice span[aria-label]"
DETAIL_CATEGORY = "button.DkEaL"
DETAIL_HOURS = 'div[data-hide-tooltip-on-mouse-move] span[aria-label]'

# Reviews section
REVIEWS_TAB = 'button[data-tab-index="1"]'
REVIEW_ITEMS = "div.jftiEf"
REVIEW_DATE = "span.rsqaWe"

# CAPTCHA / bot detection
CAPTCHA_FORM = "form#captcha-form"
RECAPTCHA_FRAME = 'iframe[src*="recaptcha"]'

# Smoke test — stable element on any Maps search page
SEARCH_BOX = 'input#searchboxinput'
