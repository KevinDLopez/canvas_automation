from typing import TypedDict, List, Dict, Any


class Answer(TypedDict, total=True):
    fileUploadAnswers: "FileUploadAnswers"
    grade: "Grade"
    questionId: str
    textAnswers: "TextAnswers"


class BatchUpdateFormRequest(TypedDict, total=True):
    includeFormInResponse: bool
    requests: List["Request"]
    writeControl: "WriteControl"


class BatchUpdateFormResponse(TypedDict, total=True):
    form: "Form"
    replies: List["Response"]
    writeControl: "WriteControl"


class ChoiceQuestion(TypedDict, total=True):
    options: List["Option"]
    shuffle: bool
    type: str


class CloudPubsubTopic(TypedDict, total=True):
    topicName: str


class CorrectAnswer(TypedDict, total=True):
    value: str


class CorrectAnswers(TypedDict, total=True):
    answers: List["CorrectAnswer"]


class CreateItemRequest(TypedDict, total=True):
    item: "Item"
    location: "Location"


class CreateItemResponse(TypedDict, total=True):
    itemId: str
    questionId: List[str]


class CreateWatchRequest(TypedDict, total=True):
    watch: "Watch"
    watchId: str


class DateQuestion(TypedDict, total=True):
    includeTime: bool
    includeYear: bool


class DeleteItemRequest(TypedDict, total=True):
    location: "Location"


class Empty(TypedDict, total=True):
    pass


class ExtraMaterial(TypedDict, total=True):
    link: "TextLink"
    video: "VideoLink"


class Feedback(TypedDict, total=True):
    material: List["ExtraMaterial"]
    text: str


class FileUploadAnswer(TypedDict, total=True):
    fileId: str
    fileName: str
    mimeType: str


class FileUploadAnswers(TypedDict, total=True):
    answers: List["FileUploadAnswer"]


class FileUploadQuestion(TypedDict, total=True):
    folderId: str
    maxFileSize: str
    maxFiles: int
    types: List[str]


class Form(TypedDict, total=True):
    formId: str
    info: "Info"
    items: List["Item"]
    linkedSheetId: str
    responderUri: str
    revisionId: str
    settings: "FormSettings"


class FormResponse(TypedDict, total=True):
    answers: Dict[str, Any]
    createTime: str
    formId: str
    lastSubmittedTime: str
    respondentEmail: str
    responseId: str
    totalScore: float


class FormSettings(TypedDict, total=True):
    quizSettings: "QuizSettings"


class Grade(TypedDict, total=True):
    correct: bool
    feedback: "Feedback"
    score: float


class Grading(TypedDict, total=True):
    correctAnswers: "CorrectAnswers"
    generalFeedback: "Feedback"
    pointValue: int
    whenRight: "Feedback"
    whenWrong: "Feedback"


class Grid(TypedDict, total=True):
    columns: "ChoiceQuestion"
    shuffleQuestions: bool


class Image(TypedDict, total=True):
    altText: str
    contentUri: str
    properties: "MediaProperties"
    sourceUri: str


class ImageItem(TypedDict, total=True):
    image: "Image"


class Info(TypedDict, total=True):
    description: str
    documentTitle: str
    title: str


class Item(TypedDict, total=True):
    description: str
    imageItem: "ImageItem"
    itemId: str
    pageBreakItem: "PageBreakItem"
    questionGroupItem: "QuestionGroupItem"
    questionItem: "QuestionItem"
    textItem: "TextItem"
    title: str
    videoItem: "VideoItem"


class ListFormResponsesResponse(TypedDict, total=True):
    nextPageToken: str
    responses: List["FormResponse"]


class ListWatchesResponse(TypedDict, total=True):
    watches: List["Watch"]


class Location(TypedDict, total=True):
    index: int


class MediaProperties(TypedDict, total=True):
    alignment: str
    width: int


class MoveItemRequest(TypedDict, total=True):
    newLocation: "Location"
    originalLocation: "Location"


class Option(TypedDict, total=True):
    goToAction: str
    goToSectionId: str
    image: "Image"
    isOther: bool
    value: str


class PageBreakItem(TypedDict, total=True):
    pass


class Question(TypedDict, total=True):
    choiceQuestion: "ChoiceQuestion"
    dateQuestion: "DateQuestion"
    fileUploadQuestion: "FileUploadQuestion"
    grading: "Grading"
    questionId: str
    required: bool
    rowQuestion: "RowQuestion"
    scaleQuestion: "ScaleQuestion"
    textQuestion: "TextQuestion"
    timeQuestion: "TimeQuestion"


class QuestionGroupItem(TypedDict, total=True):
    grid: "Grid"
    image: "Image"
    questions: List["Question"]


class QuestionItem(TypedDict, total=True):
    image: "Image"
    question: "Question"


class QuizSettings(TypedDict, total=True):
    isQuiz: bool


class RenewWatchRequest(TypedDict, total=True):
    pass


class Request(TypedDict, total=False):
    createItem: "CreateItemRequest"
    deleteItem: "DeleteItemRequest"
    moveItem: "MoveItemRequest"
    updateFormInfo: "UpdateFormInfoRequest"
    updateItem: "UpdateItemRequest"
    updateSettings: "UpdateSettingsRequest"


class Response(TypedDict, total=True):
    createItem: "CreateItemResponse"


class RowQuestion(TypedDict, total=True):
    title: str


class ScaleQuestion(TypedDict, total=True):
    high: int
    highLabel: str
    low: int
    lowLabel: str


class TextAnswer(TypedDict, total=True):
    value: str


class TextAnswers(TypedDict, total=True):
    answers: List["TextAnswer"]


class TextItem(TypedDict, total=True):
    pass


class TextLink(TypedDict, total=True):
    displayText: str
    uri: str


class TextQuestion(TypedDict, total=True):
    paragraph: bool


class TimeQuestion(TypedDict, total=True):
    duration: bool


class UpdateFormInfoRequest(TypedDict, total=True):
    info: "Info"
    updateMask: str


class UpdateItemRequest(TypedDict, total=True):
    item: "Item"
    location: "Location"
    updateMask: str


class UpdateSettingsRequest(TypedDict, total=True):
    settings: "FormSettings"
    updateMask: str


class Video(TypedDict, total=True):
    properties: "MediaProperties"
    youtubeUri: str


class VideoItem(TypedDict, total=True):
    caption: str
    video: "Video"


class VideoLink(TypedDict, total=True):
    displayText: str
    youtubeUri: str


class Watch(TypedDict, total=True):
    createTime: str
    errorType: str
    eventType: str
    expireTime: str
    id: str
    state: str
    target: "WatchTarget"


class WatchTarget(TypedDict, total=True):
    topic: "CloudPubsubTopic"


class WriteControl(TypedDict, total=True):
    requiredRevisionId: str
    targetRevisionId: str
