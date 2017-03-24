#Paystack settings

class PaystackConfig():
    PAYSTACK_URL = "https://api.paystack.co"

    SECRET_KEY = "sk_test_19913a9f729355af025cabb9d2097d88763d49d8"

    PUBLIC_KEY = "pk_test_3b618f2ab4eda42dc65da2546c85163307e12bfe"

    PASS_ON_TRANSACTION_COST = True

    LOCAL_COST = 0.015
    INTL_COST = 0.039

    def __new__(cls):
        raise TypeError("Can not make instance of class")
    