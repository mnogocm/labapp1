import json
import xml.etree.ElementTree as ET
from typing import List, Optional


class RecipeException(Exception):
    """Ошибка при работе с кулинарными рецептами."""


class Product:
    """Ингредиент рецепта."""

    def __init__(self, title: str, quantity: float, measure: str):
        if not title.strip():
            raise RecipeException("У ингредиента должно быть название.")
        if quantity <= 0:
            raise RecipeException("Количество должно быть больше нуля.")
        if not measure.strip():
            raise RecipeException("Укажите единицу измерения.")
        self.title = title
        self.quantity = quantity
        self.measure = measure

    def to_dict(self) -> dict:
        return {"title": self.title, "quantity": self.quantity, "measure": self.measure}

    @classmethod
    def from_dict(cls, data: dict) -> "Product":
        return cls(str(data["title"]), float(data["quantity"]), str(data["measure"]))

    def __str__(self) -> str:
        return f"{self.title}: {self.quantity:g} {self.measure}"


class CookingStep:
    """Отдельный шаг приготовления."""

    def __init__(self, position: int, text: str):
        if position < 1:
            raise RecipeException("Номер шага должен быть положительным.")
        if not text.strip():
            raise RecipeException("Описание шага не может быть пустым.")
        self.position = position
        self.text = text

    def to_dict(self) -> dict:
        return {"position": self.position, "text": self.text}

    @classmethod
    def from_dict(cls, data: dict) -> "CookingStep":
        return cls(int(data["position"]), str(data["text"]))

    def __str__(self) -> str:
        return f"{self.position}. {self.text}"


class DishRecipe:
    """Данные одного рецепта."""

    def __init__(self, number: int, title: str, category: str,
                 minutes: int, servings: int,
                 products: Optional[List[Product]] = None,
                 steps: Optional[List[CookingStep]] = None):
        if number <= 0:
            raise RecipeException("Номер рецепта должен быть больше нуля.")
        if not title.strip():
            raise RecipeException("Название рецепта не может быть пустым.")
        if minutes <= 0 or servings <= 0:
            raise RecipeException("Время и количество порций должны быть больше нуля.")
        self.number = number
        self.title = title
        self.category = category
        self.minutes = minutes
        self.servings = servings
        self.products = products if products is not None else []
        self.steps = steps if steps is not None else []

    def add_product(self, product: Product) -> None:
        self.products.append(product)

    def add_step(self, step: CookingStep) -> None:
        self.steps.append(step)

    def to_dict(self) -> dict:
        return {
            "number": self.number, "title": self.title,
            "category": self.category, "minutes": self.minutes,
            "servings": self.servings,
            "products": [item.to_dict() for item in self.products],
            "steps": [item.to_dict() for item in self.steps]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DishRecipe":
        products = [Product.from_dict(item) for item in data.get("products", [])]
        steps = [CookingStep.from_dict(item) for item in data.get("steps", [])]
        return cls(int(data["number"]), str(data["title"]),
                   str(data.get("category", "Без категории")),
                   int(data["minutes"]), int(data["servings"]), products, steps)

    def __str__(self) -> str:
        return (f"№{self.number}: {self.title} | {self.category} | "
                f"{self.minutes} мин. | порций: {self.servings}")


class Cookbook:
    """Хранилище рецептов с операциями CRUD и работой с файлами."""

    def __init__(self):
        self.recipes: List[DishRecipe] = []

    def find(self, number: int) -> Optional[DishRecipe]:
        for recipe in self.recipes:
            if recipe.number == number:
                return recipe
        return None

    def get_all(self) -> List[DishRecipe]:
        return self.recipes.copy()

    def add(self, recipe: DishRecipe) -> None:
        if self.find(recipe.number) is not None:
            raise RecipeException("Рецепт с таким номером уже существует.")
        self.recipes.append(recipe)

    def update(self, number: int, title: str, category: str,
               minutes: int, servings: int) -> None:
        recipe = self.find(number)
        if recipe is None:
            raise RecipeException("Рецепт не найден.")
        if not title.strip():
            raise RecipeException("Название не может быть пустым.")
        if minutes <= 0 or servings <= 0:
            raise RecipeException("Время и порции должны быть больше нуля.")
        recipe.title = title
        recipe.category = category
        recipe.minutes = minutes
        recipe.servings = servings

    def delete(self, number: int) -> None:
        recipe = self.find(number)
        if recipe is None:
            raise RecipeException("Рецепт не найден.")
        self.recipes.remove(recipe)

    def save_json(self, filename: str) -> None:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump([item.to_dict() for item in self.recipes], file,
                      ensure_ascii=False, indent=4)

    def load_json(self, filename: str) -> None:
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
            self.recipes = [DishRecipe.from_dict(item) for item in data]
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise RecipeException(f"Не удалось загрузить JSON: {error}") from error

    def save_xml(self, filename: str) -> None:
        root = ET.Element("cookbook")
        for recipe in self.recipes:
            node = ET.SubElement(root, "recipe")
            for key, value in (("number", recipe.number), ("title", recipe.title),
                               ("category", recipe.category), ("minutes", recipe.minutes),
                               ("servings", recipe.servings)):
                ET.SubElement(node, key).text = str(value)
            products_node = ET.SubElement(node, "products")
            for product in recipe.products:
                item_node = ET.SubElement(products_node, "product")
                for key, value in (("title", product.title), ("quantity", product.quantity),
                                   ("measure", product.measure)):
                    ET.SubElement(item_node, key).text = str(value)
            steps_node = ET.SubElement(node, "steps")
            for step in recipe.steps:
                step_node = ET.SubElement(steps_node, "step")
                ET.SubElement(step_node, "position").text = str(step.position)
                ET.SubElement(step_node, "text").text = step.text
        tree = ET.ElementTree(root)
        ET.indent(tree, space="    ")
        tree.write(filename, encoding="utf-8", xml_declaration=True)

    def load_xml(self, filename: str) -> None:
        try:
            root = ET.parse(filename).getroot()
            loaded = []
            for node in root.findall("recipe"):
                products = [Product(
                    item.findtext("title", ""), float(item.findtext("quantity", "0")),
                    item.findtext("measure", ""))
                    for item in node.findall("./products/product")]
                steps = [CookingStep(int(item.findtext("position", "0")),
                                     item.findtext("text", ""))
                         for item in node.findall("./steps/step")]
                loaded.append(DishRecipe(
                    int(node.findtext("number", "0")), node.findtext("title", ""),
                    node.findtext("category", "Без категории"),
                    int(node.findtext("minutes", "0")),
                    int(node.findtext("servings", "0")), products, steps))
            self.recipes = loaded
        except (OSError, ET.ParseError, RecipeException, TypeError, ValueError) as error:
            raise RecipeException(f"Не удалось загрузить XML: {error}") from error


def make_examples() -> Cookbook:
    book = Cookbook()
    soup = DishRecipe(1, "Овощной суп", "Первое блюдо", 40, 3)
    soup.add_product(Product("Картофель", 3, "шт."))
    soup.add_product(Product("Морковь", 1, "шт."))
    soup.add_product(Product("Вода", 1.5, "л"))
    soup.add_step(CookingStep(1, "Нарезать овощи."))
    soup.add_step(CookingStep(2, "Варить овощи в воде до готовности."))
    salad = DishRecipe(2, "Овощной салат", "Салат", 15, 2)
    salad.add_product(Product("Помидоры", 2, "шт."))
    salad.add_product(Product("Огурцы", 2, "шт."))
    salad.add_step(CookingStep(1, "Нарезать овощи и перемешать."))
    book.add(soup)
    book.add(salad)
    return book


def show_recipe(recipe: DishRecipe) -> None:
    print(recipe)
    print("  Ингредиенты:")
    for product in recipe.products:
        print("   -", product)
    print("  Шаги:")
    for step in recipe.steps:
        print("   ", step)


def print_menu() -> None:
    print("\n--- Кулинарная книга ---")
    print("1. Показать рецепты\n2. Найти рецепт\n3. Добавить рецепт")
    print("4. Изменить рецепт\n5. Удалить рецепт\n6. Сохранить JSON")
    print("7. Загрузить JSON\n8. Сохранить XML\n9. Загрузить XML\n0. Выход")


def main() -> None:
    book = make_examples()
    while True:
        print_menu()
        try:
            choice = input("Ваш выбор: ").strip()
            if choice == "1":
                if not book.get_all():
                    print("Рецептов пока нет.")
                for recipe in book.get_all():
                    show_recipe(recipe)
            elif choice == "2":
                recipe = book.find(int(input("Номер рецепта: ")))
                print("Рецепт не найден." if recipe is None else "")
                if recipe is not None:
                    show_recipe(recipe)
            elif choice == "3":
                number = int(input("Номер: "))
                title = input("Название: ").strip()
                category = input("Категория: ").strip()
                minutes = int(input("Время приготовления в минутах: "))
                servings = int(input("Количество порций: "))
                book.add(DishRecipe(number, title, category, minutes, servings))
                print("Рецепт добавлен.")
            elif choice == "4":
                number = int(input("Номер изменяемого рецепта: "))
                title = input("Новое название: ").strip()
                category = input("Новая категория: ").strip()
                minutes = int(input("Время приготовления: "))
                servings = int(input("Количество порций: "))
                book.update(number, title, category, minutes, servings)
                print("Рецепт изменён.")
            elif choice == "5":
                book.delete(int(input("Номер удаляемого рецепта: ")))
                print("Рецепт удалён.")
            elif choice in ("6", "7", "8", "9"):
                is_xml = choice in ("8", "9")
                default_name = "cookbook.xml" if is_xml else "cookbook.json"
                filename = input(f"Имя файла [{default_name}]: ").strip() or default_name
                if choice == "6":
                    book.save_json(filename)
                elif choice == "7":
                    book.load_json(filename)
                elif choice == "8":
                    book.save_xml(filename)
                else:
                    book.load_xml(filename)
                print("Операция с файлом выполнена.")
            elif choice == "0":
                print("До свидания!")
                break
            else:
                print("Такого пункта нет.")
        except ValueError:
            print("Ошибка: проверьте введённые числа.")
        except RecipeException as error:
            print("Ошибка:", error)
        except OSError as error:
            print("Ошибка файла:", error)


if __name__ == "__main__":
    main()
