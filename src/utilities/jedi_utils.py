import jedi
from src.common.definitions import ProjectContext, Symbol
from src.utilities.paths import add_path_to_prefix, remove_path_prefix


def goto_symbol(context: ProjectContext, symbol: Symbol):
    path = add_path_to_prefix(context.folder_path, symbol.file_location)
    line = symbol.line
    column = symbol.column
    jedi_script = jedi.Script(path=path)
    definition = jedi_script.goto(line, column)
    return definition[0]


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


def get_body_of_symbol(symbol: Symbol, context: ProjectContext):
    name = goto_symbol(context, symbol)
    # Load the file
    path = name.module_path

    (start, _) = name.get_definition_start_position()
    (end, _) = name.get_definition_end_position()
    with open(path, "r") as file:
        code = file.readlines()
        #    Get the code
        return "\n".join(code[start - 1 : end + 1])
