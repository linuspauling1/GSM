from gotify import Gotify

gotify = Gotify(
    base_url='http://localhost:80',
    app_token='A_8APqsvE8C5Rom',
)

gotify.create_message(
    message='Hello pula in cur!',
    title='Hello pula',
)
