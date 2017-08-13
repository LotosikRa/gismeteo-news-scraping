import loggingfrom scrapy.selector import SelectorList, Selectorlogger = logging.getLogger(__name__)# media typesPARAGRAPH_TYPE = 'paragraph'SOCIAL_TYPE = 'social'VIDEO_TYPE = 'video'PHOTO_TYPE = 'photo'ERROR_TYPE = 'ERROR'MEDIA_TYPES_ORDER = [PARAGRAPH_TYPE, PHOTO_TYPE, VIDEO_TYPE, SOCIAL_TYPE,                     ERROR_TYPE]# formattingOPEN_CHAR = '<'CLOSE_CHAR = '>'ESCAPE_CHAR_PAIRS = [    ('\x97', '-'), ('\xa0', ' '),  # special bytes    ('\r\n\t', ''), ('\t', ''), ('\n', ''), ('\r', ''),  # spacing]class MediaCounter(dict):    media_types_order = MEDIA_TYPES_ORDER    open_char = OPEN_CHAR    close_char = CLOSE_CHAR    summary_message = 'Summary :: '    separator = '; '    message_format = '{media_type}: {counter}'    def __init__(self):        self._string = ''        self._is_closed = False        super().__init__({mt: 0 for mt in self.media_types_order})    @property    def string(self) -> str:        sequence = list(self.generator())        lenght = len(sequence)        new_string = ''        if lenght != 0:            new_string += self.open_char            new_string += self.summary_message            new_string += sequence[0]            if lenght > 1:                for i in sequence[1:]:                    new_string += self.separator + i            new_string += self.close_char        self.string = new_string        return new_string    @string.setter    def string(self, value):        assert isinstance(value, str)        self._string = value    def add_video(self):        self[VIDEO_TYPE] += 1    def add_photo(self):        self[PHOTO_TYPE] += 1    def add_social(self):        self[SOCIAL_TYPE] += 1    def add_error(self):        self[ERROR_TYPE] += 1    def add_paragraph(self):        self[PARAGRAPH_TYPE] += 1    def generator(self):        for media_type in self.media_types_order:            counter = self[media_type]            if counter > 0:                yield self.message_format.format(                    media_type=media_type, counter=counter)    def summary(self) -> str:        if self._is_closed:            raise RuntimeError('MediaCounter is already closed.')        self._is_closed = True        return self.string    def __str__(self):        return self.string    def __repr__(self):        return '<MediaCounter ' + self.string[1:]class Element:    media_types = set(MEDIA_TYPES_ORDER)    non_empty_media_types = {ERROR_TYPE, PARAGRAPH_TYPE}    open_char = OPEN_CHAR    close_char = CLOSE_CHAR    def __init__(self, media_type: str, string: str or None =None):        if not isinstance(media_type, str):            raise TypeError('`media_type` argument must be `str` object.')        if media_type not in self.media_types:            raise ValueError('`media_type` must have one of the following '                             'values: {}'.format(self.media_types))        if media_type in self.non_empty_media_types and not string:            raise ValueError('For "{}" media type `string` must not be empty'                             .format(media_type))        elif not isinstance(string, str) and string is not None:            raise TypeError('`string` argument must be `str` object.')        self.string = string        self.media_type = media_type    def is_empty(self):        return self.string is None    def __repr__(self):        return '<Element media_type: "{}" string: "{}">'.format(            self.media_type, self.string)    def __str__(self):        if self.media_type == PARAGRAPH_TYPE:            return self.string        else:            return self.open_char + self.media_type + \                   (' ' + self.string if self.string else '') + self.close_charclass Combo:    open_char = OPEN_CHAR    close_char = CLOSE_CHAR    multiple_template = ' X{}'    def __init__(self, chain):        assert isinstance(chain, ElementsChain)        self.chain = chain        self.media_type = None        self.count = 0    def start(self, element: Element):        """ Starts new combo. """        self.media_type = element.media_type        self.increase()    def drop(self):        """ Writes all saved elements to chain. """        if self.count > 0 and self.media_type:            self.chain.add_combo(self)            self.media_type = None            self.count = 0    def increase(self):        """ Appends the element to self. """        self.count += 1    def process(self, element: Element) -> bool:        """        Decides either to continue the combo, or drop existed and        start the new one.        :param element:        :return: `True` if combo continues, else `False`        """        if element.media_type == self.media_type:            self.increase()            return True        else:            if self.media_type:                self.drop()            self.start(element)            return False    def __repr__(self):        return '<Combo media_type: {} count: {}>'.format(            self.media_type, self.count)    def __str__(self):        return self.open_char + self.media_type + \               (self.multiple_template.format(self.count)                if self.count > 1 else '') + self.close_charclass ElementsChain(list):    def __init__(self, media_counter=None):        if not media_counter:            media_counter = MediaCounter()        self._is_closed = False        self.media_counter = media_counter        self.combo = Combo(self)        super().__init__()    def append(self, object):        if self._is_closed:            raise RuntimeError('ElementsChin is already closed.')        super().append(object)    def add_element(self, element: Element):        if element.is_empty():            self.combo.process(element)        else:            self.combo.drop()            self.append(str(element))    def add_paragraph(self, paragraph: str):        self.add_element(Element(string=paragraph, media_type=PARAGRAPH_TYPE))        self.media_counter.add_paragraph()    def add_error(self, extra: str =None):        self.add_element(Element(string=extra, media_type=ERROR_TYPE))        self.media_counter.add_error()    def add_social(self, extra: str =None):        self.add_element(Element(string=extra, media_type=SOCIAL_TYPE))        self.media_counter.add_social()    def add_photo(self, extra: str =None):        self.add_element(Element(string=extra, media_type=PHOTO_TYPE))        self.media_counter.add_photo()    def add_video(self, extra: str =None):        self.add_element(Element(string=extra, media_type=VIDEO_TYPE))        self.media_counter.add_video()    def add_combo(self, combo: Combo):        self.append(str(combo))    def add_summary(self):        self.combo.drop()        self.append(self.media_counter.summary())    def close(self) -> list:        self._is_closed = True        return list(self)# TODO: write itclass Clearer:    hyperlink_format = '[{link}]({href})'    open_char = OPEN_CHAR    close_char = CLOSE_CHAR    escape_chars = ESCAPE_CHAR_PAIRS    wrap_chars = [' ', '\n', '\t', '\r']    @classmethod    def unwrap_single_text(cls, text: str):        while True:            if len(text) == 0:                return text            if text[0] in cls.wrap_chars:                text = text[1:]            elif text[-1] in cls.wrap_chars:                text = text[:-1]            else:                return text    @classmethod    def remove_internal_tags(cls, element: SelectorList, tag: str):        if not isinstance(tag, str):            raise TypeError('`tag` is not `str` object.')        _LINK = 'link'        _BOLD = 'bold'        _SPAN = 'span'        string = ''        just_text_list = element.css('{}::text'.format(tag)).extract()        # define other tags        href_selector = element.css('{} > a::attr(href)'.format(tag))        link_selector = element.css('{} > a::text'.format(tag))        bold_selector = element.css('{} > strong::text'.format(tag))        span_selector = element.css('{} > span::text'.format(tag))        # check if every link have text        href_length = len(href_selector)        if href_length > len(link_selector):            raise RuntimeError('More hyper-references than texts for them.')        # create iterable        iterable = list(zip(            link_selector.extract(),            [_LINK for _ in range(href_length)],            href_selector.extract(), ))        iterable.extend(list(zip(            bold_selector.extract(),            [_BOLD for _ in range(len(bold_selector))], )))        iterable.extend(list(zip(            span_selector.extract(),            [_SPAN for _ in range(len(span_selector))], )))        # iterate over        for text_fragment in element.css('::text').extract():            if text_fragment in just_text_list:                string += text_fragment            else:                for text, typ, *args in iterable:                    if text == text_fragment:                        # parsing logic                        if typ == _LINK:                            string += cls.hyperlink_format.format(                                link=text, href=args[0])                        elif typ == _BOLD:                            string += text                        elif typ == _SPAN:                            string += text                        break        return string    @classmethod    def is_trash(cls, string: str) -> bool:        lst = [' ']        for i, _ in cls.escape_chars:            lst.append(i)        for i in lst:            string = string.replace(i, '')        if string == '':            return True        else:            return Falseclass Parser:    def __init__(self, elements_chain: ElementsChain =None,                 media_counter: MediaCounter =None,                 add_summary: bool =True):        if not media_counter:            media_counter = MediaCounter()        if not elements_chain:            elements_chain = ElementsChain(media_counter)        self.chain = self.elements_chain = elements_chain        self.media_counter = media_counter        self.add_summary = add_summary        self.clearer = Clearer()    def _raise_unknown_block(self, selector: SelectorList):        raise ValueError('Unknown HTML block: {}'.format(selector.extract()))    def parse(self, selector: SelectorList) -> None:        raise NotImplementedError    def safe_parse(self, selector: SelectorList) -> None:        try:            self.parse(selector)        except Exception as exc:            logger.exception(exc)            self.elements_chain.add_error(str(exc))    def close(self) -> list:        if self.add_summary:            self.elements_chain.add_summary()        return self.elements_chain.close()    parsed_list = close    # shortcuts    def parse_text(self, text_selector: SelectorList, tag: str):        if isinstance(text_selector, SelectorList):            string = text_selector.extract_first()        else:            raise TypeError('Given `text_selector` is not `Selector` or '                            '`SelectorList` object.')        if not self.clearer.is_trash(string):            cleared1 = self.clearer.remove_internal_tags(text_selector, tag=tag)            if not self.clearer.is_trash(cleared1):                cleared2 = self.clearer.unwrap_single_text(cleared1)                self.chain.add_paragraph(cleared2)