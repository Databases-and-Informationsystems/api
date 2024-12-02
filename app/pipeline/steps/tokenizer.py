import typing

import nltk
from nltk.tokenize import PunktSentenceTokenizer

from app.pipeline.model.document import DocumentEditDTO, TokenDTO
from app.pipeline.step import PipelineStep, PipelineStepType


from nltk.tokenize import word_tokenize


class Tokenizer(PipelineStep):
    def __init__(self, name: str = "Tokenizer"):
        super().__init__(name, PipelineStepType.TOKENIZER)

        # Both 'punkt_tab' and 'averaged_perceptron_tagger_eng' are necessary for nltk tokenizing
        try:
            nltk.data.find("punkt_tab")
        except LookupError:
            nltk.download("punkt_tab")

        try:
            nltk.data.find("averaged_perceptron_tagger_eng")
        except LookupError:
            nltk.download("averaged_perceptron_tagger_eng")

    def _train(self):
        pass

    def _run(self, document_edit: DocumentEditDTO) -> DocumentEditDTO:
        tokenizer = PunktSentenceTokenizer()

        # Tokens where a "." does not mean the end of a sentence
        tokenizer._params.abbrev_types.update(
            ["e.g", "etc", "dr", "vs", "mr", "mrs", "prof", "inc", "i.e"]
        )
        sentences = tokenizer.tokenize(
            # ".." Is not a valid token but rather a shortcut + end of sentence
            document_edit.document.content.replace("..", ". .")
        )

        tokens: typing.List[TokenDTO] = []
        document_index = 0
        sentence_index = 0

        for sentence in sentences:
            sentence_tokens = word_tokenize(sentence)
            tagged_tokens = nltk.pos_tag(sentence_tokens)

            for token, tag in tagged_tokens:
                tokens.append(
                    TokenDTO(
                        text=token,
                        pos_tag=tag,
                        document_index=document_index,
                        sentence_index=sentence_index,
                        id=None,
                    )
                )
                document_index += 1

            sentence_index += 1

        document_edit.document.tokens = tokens
        return document_edit
