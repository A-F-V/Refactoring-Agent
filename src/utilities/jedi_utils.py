import jedi
from src.common.definitions import (
    CodeSnippet,
    CodeSpan,
    Definition,
    ProjectContext,
    Symbol,
)
from src.utilities.paths import add_path_to_prefix, remove_path_prefix


def goto_symbol(context: ProjectContext, symbol: Symbol):
    path = add_path_to_prefix(context.folder_path, symbol.file_location)
    line = symbol.line
    column = symbol.column
    jedi_script = jedi.Script(path=path)
    definition = jedi_script.goto(line, column)
    return definition[0]


def symbol_to_definition(symbol: Symbol, context: ProjectContext) -> Definition:
    name = goto_symbol(context, symbol)
    # Load the file
    path = name.module_path

    (start, _) = name.get_definition_start_position()
    (end, _) = name.get_definition_end_position()

    span = CodeSpan(
        file_location=path,
        start_line=start,
        end_line=end,
    )
    return Definition(symbol=symbol, span=span)


def jedi_name_to_symbol(name, context: ProjectContext) -> Symbol:
    (line, column) = name.line, name.column
    path = remove_path_prefix(name.module_path, context.folder_path)
    result = Symbol(
        name=str(name.name),
        file_location=str(path),
        line=int(line),
        column=int(column),
    )
    return result


def load_code(span: CodeSpan, context: ProjectContext):
    path = add_path_to_prefix(context.folder_path, span.file_location)
    start = span.start_line
    end = span.end_line
    with open(path, "r") as file:
        code = file.readlines()
        #    Get the code
        return "\n".join(code[start - 1 : end + 1])


def span_to_snippet(span: CodeSpan, context: ProjectContext) -> CodeSnippet:
    return CodeSnippet(
        {
            "file_path": span.file_location,
            "code": load_code(span, context),
            "starting_line": span.start_line,
        }
    )
