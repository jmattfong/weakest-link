class Questions :

    def __init__(self) :
        self.questions = []
        self.current_question = 0

    def add_question(self, question, answer) :
        self.questions.append((question, answer))

    def get_current_question(self) :
        return self.questions[self.current_question]

    def get_next_question(self) :
        question = self.get_current_question()
        self.current_question += 1
        return question

    def remaining_questions(self) :
        return len(self.questions) - self.current_question
