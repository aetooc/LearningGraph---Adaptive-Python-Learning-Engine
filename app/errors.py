class ApplicationError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code #http status code
        self.detail = detail #error detail
        super().__init__(detail)
