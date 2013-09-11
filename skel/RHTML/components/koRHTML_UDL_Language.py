# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See the
# License for the specific language governing rights and limitations
# under the License.
#
# The Original Code is Komodo code.
#
# The Initial Developer of the Original Code is ActiveState Software Inc.
# Portions created by ActiveState Software Inc are Copyright (C) 2000-2007
# ActiveState Software Inc. All Rights Reserved.
#
# Contributor(s):
#   ActiveState Software Inc
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

# Komodo RHTML language service.
#
# Generated by 'luddite.py' on Thu Jul  5 12:35:29 2007.
#

import re
import logging
from xpcom import components
from xpcom.server import UnwrapObject
from koXMLLanguageBase import koHTMLLanguageBase
from koLintResults import koLintResults

from codeintel2.rubycile import rails_role_from_path

import scimozindent

log = logging.getLogger("koRHTMLLanguage")
# log.setLevel(logging.DEBUG)


def registerLanguage(registry):
    log.debug("Registering language RHTML")
    registry.registerLanguage(KoRHTMLLanguage())


class KoRHTMLLanguage(koHTMLLanguageBase):
    name = "RHTML"
    lexresLangName = "RHTML"
    _reg_desc_ = "%s Language" % name
    _reg_contractid_ = "@activestate.com/koLanguage?language=%s;1" % name
    _reg_clsid_ = "{A554B7D4-7920-4BDC-BA71-5D8555B9C9DB}"
    _reg_categories_ = [("komodo-language", name)]
    defaultExtension = '.rhtml'

    lang_from_udl_family = {
        'CSL': 'JavaScript', 'TPL': 'RHTML', 'M': 'HTML', 'CSS': 'CSS', 'SSL': 'Ruby'}

    sample = """<ul>
<% @products.each do |p| %>
  <li><%=  @p.name %></li>
<% end %>
</ul>
"""

    def insertInternalNewline_Special(self, scimoz, indentStyle, currentPos,
                                      allowExtraNewline, style_info):
        """
        Split %|% so the %'s are on separate lines, and there's a blank line
        in the middle.
        """
        if indentStyle is None or currentPos < 2:
            return None
        if scimoz.getStyleAt(currentPos) != scimoz.SCE_UDL_TPL_OPERATOR:
            return None
        percentChar = ord("%")
        if scimoz.getCharAt(currentPos) != percentChar:
            return None
        prevPos = currentPos - 1  # ascii
        if scimoz.getStyleAt(prevPos) != scimoz.SCE_UDL_TPL_OPERATOR:
            return None
        if scimoz.getCharAt(prevPos) != percentChar:
            return None
        prev2Pos = prevPos - 1
        if scimoz.getStyleAt(prev2Pos) != scimoz.SCE_UDL_TPL_OPERATOR:
            return None
        if scimoz.getCharAt(prev2Pos) != ord("<"):
            return None
        lineNo = scimoz.lineFromPosition(currentPos)
        closeIndentWidth = self._getIndentWidthForLine(scimoz, lineNo)
        if indentStyle == 'smart':
            """
            i<%|% ==>

            i<%
            i....<|>
            i%

            where "i" denotes the current leading indentation
            """
            intermediateLineIndentWidth = self._getNextLineIndent(
                scimoz, lineNo)
        else:
            """
            i<%|% ==>

            i<%
            i<|>
            i%

            Note that the indentation of inner attr lines are ignored, even in block-indent mode:
            i<foo
            i........attr="val">|</foo> =>

            i<foo
            i........attr="val">
            i</foo>
            """
            intermediateLineIndentWidth = closeIndentWidth

        currentEOL = eollib.eol2eolStr[eollib.scimozEOL2eol[scimoz.eOLMode]]
        textToInsert = currentEOL + scimozindent.makeIndentFromWidth(
            scimoz, intermediateLineIndentWidth)
        finalPosn = currentPos + len(textToInsert)  # ascii-safe
        if allowExtraNewline:
            textToInsert += currentEOL + \
                scimozindent.makeIndentFromWidth(scimoz, closeIndentWidth)
        scimoz.addText(len(textToInsert), textToInsert)  # ascii-safe
        return finalPosn

    def computeIndent(self, scimoz, indentStyle, continueComments):
        return self._computeIndent(scimoz, indentStyle, continueComments, self._style_info)

    def _computeIndent(self, scimoz, indentStyle, continueComments, style_info):
        res = self._doIndentHere(
            scimoz, indentStyle, continueComments, style_info)
        if res is None:
            return koHTMLLanguageBase.computeIndent(self, scimoz, indentStyle, continueComments)
        return res

    def _keyPressed(self, ch, scimoz, style_info):
        res = self._doKeyPressHere(ch, scimoz, style_info)
        if res is None:
            return koHTMLLanguageBase._keyPressed(self, ch, scimoz, style_info)
        return res

    _startWords = "begin case else elsif ensure for if rescue unless until while".split(
        " ")

    def _doIndentHere(self, scimoz, indentStyle, continueComments, style_info):
        pos = scimoz.positionBefore(scimoz.currentPos)
        startPos = scimoz.currentPos
        style = scimoz.getStyleAt(pos)
        if style != scimoz.SCE_UDL_TPL_OPERATOR:
            return None
        if scimoz.getWCharAt(pos) != ">":
            return None
        pos -= 1
        style = scimoz.getStyleAt(pos)
        if style != scimoz.SCE_UDL_TPL_OPERATOR:
            return None
        if scimoz.getWCharAt(pos) != "%":
            return None
        curLineNo = scimoz.lineFromPosition(pos)
        lineStartPos = scimoz.positionFromLine(curLineNo)
        delta, numTags = self._getTagDiffDelta(scimoz, lineStartPos, startPos)
        if delta < 0 and numTags == 1 and curLineNo > 0:
            didDedent, dedentAmt = self.dedentThisLine(
                scimoz, curLineNo, startPos)
            if didDedent:
                return dedentAmt
            else:
                # Since RHTML tags end with a ">", keep the
                # HTML auto-indenter out of here.
                return self._getRawIndentForLine(scimoz, curLineNo)
        indentWidth = self._getIndentWidthForLine(scimoz, curLineNo)
        indent = scimoz.indent
        newIndentWidth = indentWidth + delta * indent
        if newIndentWidth < 0:
            newIndentWidth = 0
        # qlog.debug("new indent width: %d", newIndentWidth)
        return scimozindent.makeIndentFromWidth(scimoz, newIndentWidth)

    def _doKeyPressHere(self, ch, scimoz, style_info):
        # Returns either None or an indent string
        pos = scimoz.positionBefore(scimoz.currentPos)
        startPos = scimoz.currentPos
        style = scimoz.getStyleAt(pos)
        if style != scimoz.SCE_UDL_TPL_OPERATOR:
            return None
        if scimoz.getWCharAt(pos) != ">":
            return None
        pos -= 1
        curLineNo = scimoz.lineFromPosition(pos)
        lineStartPos = scimoz.positionFromLine(curLineNo)
        delta, numTags = self._getTagDiffDelta(scimoz, lineStartPos, startPos)
        if delta < 0 and numTags == 1 and curLineNo > 0:
            didDedent, dedentAmt = self.dedentThisLine(
                scimoz, curLineNo, startPos)
            if didDedent:
                return dedentAmt
        # Assume the tag's indent level is fine, so don't let the
        # HTML auto-indenter botch things up.
        return self._getRawIndentForLine(scimoz, curLineNo)

    def _getTagDiffDelta(self, scimoz, lineStartPos, startPos):
        data = scimoz.getStyledText(lineStartPos, startPos)
        chars = data[0::2]
        styles = [ord(x) for x in data[1::2]]
        lim = len(styles)
        delta = 0
        numTags = 0
        i = 0
        limSub1 = lim - 1
        while i < limSub1:
            if (styles[i] == scimoz.SCE_UDL_TPL_OPERATOR
                and styles[i + 1] == scimoz.SCE_UDL_TPL_OPERATOR
                and chars[i] == '<'
                    and chars[i + 1] == "%"):
                j = i + 2
                while (j < lim
                       and styles[j] == scimoz.SCE_UDL_SSL_DEFAULT):
                    j += 1
                if styles[j] != scimoz.SCE_UDL_SSL_WORD:
                    i = j + 1
                    continue
                wordStart = j
                while (j < lim
                       and styles[j] == scimoz.SCE_UDL_SSL_WORD):
                    j += 1
                word = chars[wordStart:j]
                if word == 'end':
                    numTags += 1
                    delta -= 1
                elif word in self._startWords:
                    numTags += 1
                    delta += 1
                i = j
            else:
                i += 1
        return delta, numTags


class KoRHTMLLinter(object):
    _com_interfaces_ = [components.interfaces.koILinter]
    _reg_desc_ = "RHTML Template Linter"
    _reg_clsid_ = "{c7f2d724-5991-4df3-965b-12db942a4ad2}"
    _reg_contractid_ = "@activestate.com/koLinter?language=RHTML;1"
    _reg_categories_ = [
        ("category-komodo-linter", 'RHTML'),
    ]

    def __init__(self):
        koLintService = components.classes["@activestate.com/koLintService;1"].getService(
            components.interfaces.koILintService)
        self._ruby_linter = UnwrapObject(
            koLintService.getLinterForLanguage("Ruby"))
        self._html_linter = koLintService.getLinterForLanguage("HTML")

    _RHTMLMatcher = re.compile(r'''(
                                (?:<%=?.*?(?:-?%>|$))
                                |(?:[^<]+|(?:<(?!%)))+ # Other non-RHTML
                                |.)''',                  # Catchall
                               re.VERBOSE | re.DOTALL)

    _blockTagRE = re.compile(r'(<%)(=?)(.*?)((?:-?%>|$))', re.DOTALL)

    def _fixRubyPart(self, text):
        parts = self._RHTMLMatcher.findall(text)
        if not parts:
            return ""
        i = 0
        lim = len(parts)
        rubyTextParts = []
        while i < lim:
            part = parts[i]
            if part.startswith("<%"):
                m = self._blockTagRE.match(part)
                if not m:
                    rubyTextParts.append(self._spaceOutNonNewlines(part))
                else:
                    emitText = m.group(2) == "="
                    log.debug(
                        "part %d: part:%s, emitText:%r", i, part, emitText)
                    rubyTextParts.append(self._spaceOutNonNewlines(m.group(1)))
                    if emitText:
                        rubyTextParts.append(
                            self._spaceOutNonNewlines(' puts '))
                    else:
                        rubyTextParts.append(' ')
                    rubyTextParts.append(m.group(3))
                    rubyTextParts.append(self._spaceOutNonNewlines(m.group(4)))
                    if emitText:
                        rubyTextParts.append(self._spaceOutNonNewlines('; '))
            else:
                rubyTextParts.append(self._spaceOutNonNewlines(part))
            i += 1
        return "".join(rubyTextParts)

    _nonNewlineMatcher = re.compile(r'[^\r\n]')

    def _spaceOutNonNewlines(self, markup):
        return self._nonNewlineMatcher.sub(' ', markup)

    _tplPatterns = ("RHTML", re.compile('<%='), re.compile(
        r'%>\s*\Z', re.DOTALL), 'puts(', ');')

    def lint(self, request):
        # With the "squelching" the multi-language linter does to pull
        # <% and %>-like tokens out of the lint input stream, there's no
        # need to map all Ruby code to RHTML
        if rails_role_from_path(request.koDoc.displayPath):
            TPLInfo = list(self._tplPatterns) + [{"supportRERB": True}]
        else:
            TPLInfo = self._tplPatterns
        return UnwrapObject(self._html_linter).lint(request, TPLInfo=TPLInfo)

    def lint_with_text(self, request, text):
        log.debug("rhtml lint: %s", text)
        rubyText = self._fixRubyPart(text)
        if not rubyText.strip():
            return
        rubyLintResults = self._resetLines(
            self._ruby_linter.lint_with_text(request, rubyText),
            text)
        return rubyLintResults

    def _resetLines(self, lintResults, text):
        lines = text.splitlines()
        fixedResults = koLintResults()
        for res in lintResults.getResults():
            try:
                targetLine = lines[res.lineEnd - 1]
            except IndexError:
                log.exception("can't index %d lines at %d", len(
                    lines), res.lineEnd - 1)
                pass  # Keep the original lintResult
            else:
                if res.columnEnd > len(targetLine):
                    res.columnEnd = len(targetLine)
            fixedResults.addResult(res)
        return fixedResults
